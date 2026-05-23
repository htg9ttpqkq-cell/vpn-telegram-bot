import base64
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request, Response

from core.config import load_config
from core.database import Database
from services.subscription_service import SubscriptionService
from services.yookassa_service import YooKassaError, YooKassaService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VPN Payment Webhook")
config = load_config()
db = Database(config.db_path)
db.init()

yookassa: Optional[YooKassaService] = None
if config.yookassa_enabled:
    yookassa = YooKassaService(
        shop_id=config.yookassa_shop_id,
        secret_key=config.yookassa_secret_key,
        return_url=config.yookassa_return_url,
    )
    logger.info("YooKassa webhook: enabled")
else:
    logger.info("YooKassa webhook: disabled (missing shop id or secret key)")

subscriptions = SubscriptionService(db, config)


def _validate_webhook_secret(token: str) -> None:
    if not config.yookassa_webhook_secret:
        return
    if token != config.yookassa_webhook_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/webhook/yookassa")
async def yookassa_webhook(
    request: Request,
    x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
) -> Dict[str, Any]:
    if not config.yookassa_enabled or yookassa is None:
        raise HTTPException(
            status_code=503,
            detail="YooKassa is not configured",
        )
    _validate_webhook_secret(x_webhook_secret)

    payload = await request.json()
    event = payload.get("event")
    payment_object = payload.get("object", {})
    payment_id = payment_object.get("id")
    status = payment_object.get("status")
    if not payment_id:
        raise HTTPException(status_code=400, detail="payment id required")

    db.update_payment_status(payment_id, status or "unknown")
    if event != "payment.succeeded" or status != "succeeded":
        return {"ok": True, "processed": False}

    payment_record = db.get_payment_by_yookassa_id(payment_id)
    if payment_record and payment_record.status == "paid":
        return {"ok": True, "processed": True, "idempotent": True}

    try:
        verified = await yookassa.get_payment(payment_id)
    except YooKassaError as exc:
        logger.exception("Failed to verify payment %s", payment_id)
        raise HTTPException(status_code=502, detail=str(exc))

    if verified.get("status") != "succeeded":
        raise HTTPException(status_code=409, detail="payment is not succeeded")

    metadata = verified.get("metadata", {})
    try:
        user_id = int(metadata.get("user_id", "0"))
        plan = str(metadata.get("plan", ""))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="invalid metadata")
    if user_id <= 0 or not plan:
        raise HTTPException(status_code=400, detail="incomplete metadata")

    activation = await subscriptions.activate_from_payment(user_id, plan)
    db.update_payment_status(payment_id, "paid")
    await subscriptions.notify_user_about_activation(user_id, activation)
    logger.info("Payment %s completed for user %s", payment_id, user_id)
    return {"ok": True, "processed": True}


@app.get("/sub/{token}")
async def get_subscription(token: str) -> Response:
    # Ищем подписку по токену
    sub = db.get_subscription_by_token(token)
    if not sub:
        # Резервный поиск по суффиксу ссылки (для обратной совместимости)
        sub = db.get_subscription_by_link_suffix(token)

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    now = datetime.now(timezone.utc)
    if not sub.is_active or (sub.expires_at and sub.expires_at < now):
        raise HTTPException(status_code=403, detail="Subscription is inactive or expired")

    if not sub.vless_link:
        raise HTTPException(status_code=404, detail="Config not generated")

    # Имя сервера в VLESS-фрагменте берём из конфига (не хардкодим)
    server_display_name = config.primary_server.display_name
    vless_link = sub.vless_link
    if "#" in vless_link:
        vless_link = vless_link.split("#", 1)[0] + "#" + server_display_name

    content = vless_link + "\n"
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    headers = {
        "profile-title": "EDELIA | VPN",
        "Content-Disposition": (
            'attachment; filename="EDELIA | VPN"; '
            "filename*=utf-8''EDELIA%20%7C%20VPN"
        ),
        "profile-update-interval": "24",
        # Передаём заголовок всегда, чтобы Hiddify измерял пинг до VLESS-прокси,
        # а не до нашего веб-сервера (устраняет ложный пинг 600+ мс).
        # expire=0 означает «без ограничений»; при наличии реального срока — подставляем его.
        "subscription-userinfo": (
            f"upload=0; download=0; total=0; expire={int(sub.expires_at.timestamp())}"
            if sub.expires_at
            else "upload=0; download=0; total=0; expire=0"
        ),
    }

    return Response(
        content=encoded_content,
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )
