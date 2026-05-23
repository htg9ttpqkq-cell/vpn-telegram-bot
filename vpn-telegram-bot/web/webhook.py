"""FastAPI веб-приложение: эндпоинты для вебхуков ЮKassa и выдачи подписок.

Ключевые изменения:
  - YooKassa webhook: защита от Double-Spending через claim_yookassa_payment_atomic.
    Параллельные вебхуки от ЮKassa с одним payment_id обрабатываются только один раз.
  - /sub/{token}: жёсткая проверка статуса на уровне FastAPI.
    Если подписка просрочена или деактивирована — 403 без конфига, даже если
    на панели 3X-UI клиент технически ещё не отключён (защита от утечки трафика).
"""

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


# ── YooKassa Webhook ──────────────────────────────────────────────────────────

@app.post("/webhook/yookassa")
async def yookassa_webhook(
    request: Request,
    x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
) -> Dict[str, Any]:
    if not config.yookassa_enabled or yookassa is None:
        raise HTTPException(status_code=503, detail="YooKassa is not configured")

    _validate_webhook_secret(x_webhook_secret)

    payload = await request.json()
    event = payload.get("event")
    payment_object = payload.get("object", {})
    payment_id = payment_object.get("id")
    status = payment_object.get("status")

    if not payment_id:
        raise HTTPException(status_code=400, detail="payment id required")

    # Обновляем сырой статус в БД (всегда, даже для не-succeeded событий)
    db.update_payment_status(payment_id, status or "unknown")

    if event != "payment.succeeded" or status != "succeeded":
        return {"ok": True, "processed": False}

    # ── Защита от Double-Spending (Race Condition) ────────────────────────────
    # claim_yookassa_payment_atomic использует BEGIN IMMEDIATE + UPDATE WHERE
    # status NOT IN ('paid', 'processing'). Параллельные вебхуки с одним
    # payment_id получат rowcount=0 и уйдут на idempotent-ответ.
    claimed = db.claim_yookassa_payment_atomic(payment_id)
    if not claimed:
        # Платёж уже обрабатывается или обработан — идемпотентный ответ
        existing = db.get_payment_by_yookassa_id(payment_id)
        if existing and existing.status == "paid":
            logger.info("YooKassa payment %s already paid — idempotent skip", payment_id)
            return {"ok": True, "processed": True, "idempotent": True}
        # Ещё в обработке (processing) — вернём 200 чтобы ЮKassa не ретраила
        logger.warning("YooKassa payment %s is already being processed — skipping", payment_id)
        return {"ok": True, "processed": False, "reason": "already_processing"}

    # ── Верификация платежа через API ЮKassa ──────────────────────────────────
    try:
        verified = await yookassa.get_payment(payment_id)
    except YooKassaError as exc:
        # Откатываем claim обратно в pending чтобы вебхук мог быть обработан повторно
        db.update_payment_status(payment_id, "pending")
        logger.exception("Failed to verify YooKassa payment %s", payment_id)
        raise HTTPException(status_code=502, detail=str(exc))

    if verified.get("status") != "succeeded":
        db.update_payment_status(payment_id, status or "unknown")
        raise HTTPException(status_code=409, detail="payment is not succeeded")

    metadata = verified.get("metadata", {})
    try:
        user_id = int(metadata.get("user_id", "0"))
        plan = str(metadata.get("plan", ""))
    except (ValueError, TypeError):
        db.update_payment_status(payment_id, "invalid_metadata")
        raise HTTPException(status_code=400, detail="invalid metadata")

    if user_id <= 0 or not plan:
        db.update_payment_status(payment_id, "invalid_metadata")
        raise HTTPException(status_code=400, detail="incomplete metadata")

    # ── Активация подписки ────────────────────────────────────────────────────
    try:
        activation = await subscriptions.activate_from_payment(user_id, plan)
        db.update_payment_status(payment_id, "paid")
        await subscriptions.notify_user_about_activation(user_id, activation)
        logger.info("YooKassa payment %s completed for user %d", payment_id, user_id)
        return {"ok": True, "processed": True}
    except Exception as exc:
        # Откатываем в pending_review — администратор увидит и сможет подтвердить вручную
        db.update_payment_status(payment_id, "pending_review")
        logger.exception(
            "Failed to activate subscription for YooKassa payment %s (user %d)",
            payment_id, user_id,
        )
        raise HTTPException(status_code=500, detail=f"Activation failed: {exc}")


# ── Subscription Config Endpoint ──────────────────────────────────────────────

@app.get("/sub/{token}")
async def get_subscription(token: str) -> Response:
    """Выдаёт VLESS-конфиг подписки в base64.

    Жёсткая защита от утечки трафика:
    - Если подписка просрочена или деактивирована → 403.
    - Проверка происходит на уровне FastAPI независимо от состояния панели 3X-UI.
    - Это гарантирует, что даже если 3X-UI по какой-то причине не отключил
      клиента, он всё равно не получит рабочий конфиг.
    """
    # Ищем подписку по токену
    sub = db.get_subscription_by_token(token)
    if not sub:
        # Резервный поиск по суффиксу ссылки (для обратной совместимости)
        sub = db.get_subscription_by_link_suffix(token)

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    now = datetime.now(timezone.utc)

    # ── Жёсткая проверка активности (независимо от панели) ───────────────────
    if not sub.is_active:
        logger.info(
            "Sub token %s: subscription for user %d is inactive — denying config",
            token, sub.user_id,
        )
        raise HTTPException(status_code=403, detail="Subscription is inactive")

    if sub.expires_at and sub.expires_at < now:
        logger.info(
            "Sub token %s: subscription for user %d expired at %s — denying config",
            token, sub.user_id, sub.expires_at.isoformat(),
        )
        raise HTTPException(status_code=403, detail="Subscription expired")

    if not sub.vless_link:
        raise HTTPException(status_code=404, detail="Config not generated")

    # Принудительно подставляем имя сервера как фрагмент (#) VLESS-ссылки.
    # Срезаем существующий фрагмент (если есть) и всегда добавляем display_name.
    # Это исключает ситуацию когда Hiddify показывает сырой IP вместо красивого названия.
    server_display_name = config.primary_server.display_name
    vless_link = sub.vless_link.split("#", 1)[0] + "#" + server_display_name

    content = vless_link + "\n"
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    headers = {
        "profile-title": "EDELIA | VPN",
        "Content-Disposition": (
            'attachment; filename="EDELIA | VPN"; '
            "filename*=utf-8''EDELIA%20%7C%20VPN"
        ),
        "profile-update-interval": "24",
        # subscription-userinfo с expire=0 говорит Hiddify: не замеряй пинг до нашего
        # веб-сервера, измеряй напрямую до VPN-прокси. Без этого Hiddify показывает
        # 600+ мс (время ответа Python-скрипта) вместо реального пинга до VLESS-сервера.
        # Реальный срок подписки контролируется через is_active/expires_at выше, а не здесь.
        "subscription-userinfo": "upload=0; download=0; total=0; expire=0",
    }

    return Response(
        content=encoded_content,
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )
