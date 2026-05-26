"""FastAPI веб-приложение: Platega.io webhook и выдача VPN-конфигов.

  - Platega.io webhook: защита от Double-Spending через claim_platega_payment_atomic.
    Верификация через back-channel GET /transaction/{id} к Platega API.
  - /sub/{token}: жёсткая проверка статуса на уровне FastAPI.
    Если подписка просрочена или деактивирована — 403 без конфига, даже если
    на панели 3X-UI клиент технически ещё не отключён (защита от утечки трафика).
"""

import base64
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Header, HTTPException, Request, Response

from core.config import load_config
from core.database import Database
from services.subscription_service import SubscriptionService
from services.platega_service import PlategaError, PlategaService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VPN Payment Webhook")
config = load_config()
db = Database(config.db_path)
db.init()

platega = PlategaService(
    merchant_id=config.platega_merchant_id,
    secret_key=config.platega_secret_key,
    return_url=config.platega_return_url,
)
logger.info("Platega webhook: enabled (merchant_id=%s)", config.platega_merchant_id)

subscriptions = SubscriptionService(db, config)


# ── Platega.io Webhook ────────────────────────────────────────────────────────

@app.post("/webhook/platega")
async def platega_webhook(
    request: Request,
    x_merchant_id: str = Header(default="", alias="X-MerchantId"),
    x_secret: str = Header(default="", alias="X-Secret"),
) -> Dict[str, Any]:
    """Принимает колбэки от Platega.io о статусах транзакций.

    Безопасность:
    - Проверяем X-MerchantId и X-Secret из заголовков.
    - Атомарный захват транзакции (защита от Double-Spending).
    - Back-channel верификация через GET /transaction/{id}.
    """
    # Верифицируем подпись через заголовки
    if x_merchant_id != config.platega_merchant_id or x_secret != config.platega_secret_key:
        logger.warning(
            "Platega webhook: invalid credentials (merchant_id=%r)", x_merchant_id
        )
        raise HTTPException(status_code=403, detail="Forbidden")

    payload = await request.json()
    # Platega sends {"transactionId": "...", "status": "..."}
    transaction_id = str(payload.get("transactionId") or payload.get("id", ""))
    status = str(payload.get("status", "")).upper()

    if not transaction_id:
        raise HTTPException(status_code=400, detail="transaction id required")

    logger.info("Platega webhook: transaction_id=%s status=%s", transaction_id, status)

    # Обрабатываем только успешные транзакции
    if status not in ("SUCCESS", "PAID", "COMPLETED", "CONFIRMED"):
        return {"ok": True, "processed": False, "status": status}

    # ── Защита от Double-Spending ─────────────────────────────────────────────
    claimed = db.claim_platega_payment_atomic(transaction_id)
    if not claimed:
        existing = db.get_payment_by_platega_id(transaction_id)
        if existing and existing.status == "paid":
            logger.info("Platega payment %s already paid — idempotent skip", transaction_id)
            return {"ok": True, "processed": True, "idempotent": True}
        logger.warning("Platega payment %s is already being processed — skipping", transaction_id)
        return {"ok": True, "processed": False, "reason": "already_processing"}

    # ── Back-channel верификация ──────────────────────────────────────────────
    try:
        verified = await platega.get_payment(transaction_id)
    except PlategaError as exc:
        db.update_payment_status_by_platega_id(transaction_id, "pending")
        logger.exception("Failed to verify Platega payment %s", transaction_id)
        raise HTTPException(status_code=502, detail=str(exc))

    verified_status = str(verified.get("status", "")).upper()
    if verified_status not in ("SUCCESS", "PAID", "COMPLETED", "CONFIRMED"):
        db.update_payment_status_by_platega_id(transaction_id, verified_status.lower())
        raise HTTPException(status_code=409, detail="payment is not succeeded")

    # Читаем user_id и plan из payload транзакции
    raw_payload = str(verified.get("payload", ""))
    try:
        # payload format: "user_id:{user_id};plan:{plan}"
        parts = dict(p.split(":", 1) for p in raw_payload.split(";") if ":" in p)
        user_id = int(parts["user_id"])
        plan = parts["plan"]
    except Exception:
        db.update_payment_status_by_platega_id(transaction_id, "invalid_metadata")
        logger.error("Platega webhook: bad payload %r", raw_payload)
        raise HTTPException(status_code=400, detail="invalid payload format")

    if user_id <= 0 or not plan:
        db.update_payment_status_by_platega_id(transaction_id, "invalid_metadata")
        raise HTTPException(status_code=400, detail="incomplete metadata")

    # ── Активация подписки ────────────────────────────────────────────────────
    try:
        activation = await subscriptions.activate_from_payment(user_id, plan)
        db.update_payment_status_by_platega_id(transaction_id, "paid")
        await subscriptions.notify_user_about_activation(user_id, activation)
        logger.info("Platega payment %s completed for user %d", transaction_id, user_id)
        return {"ok": True, "processed": True}
    except Exception as exc:
        db.update_payment_status_by_platega_id(transaction_id, "pending_review")
        logger.exception(
            "Failed to activate subscription for Platega payment %s (user %d)",
            transaction_id, user_id,
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

    # ── Автообновление конфигурации (если изменился шаблон в .env) ───────────
    from services.vpn_provision import needs_config_refresh, generate_vless_link
    if needs_config_refresh(sub, config):
        logger.info("Sub token %s: configuration refresh needed", token)
        import secrets
        import uuid
        client_uuid = sub.client_uuid or str(uuid.uuid4())
        sub_token = sub.sub_token or secrets.token_urlsafe(16)

        vless_link = generate_vless_link(config.vless_template, client_uuid)
        db.set_subscription(
            user_id=sub.user_id,
            plan=sub.plan or "trial",
            expires_at=sub.expires_at,
            is_active=sub.is_active,
            vless_link=vless_link,
            sub_token=sub_token,
            client_uuid=client_uuid,
        )
        sub.vless_link = vless_link
        sub.client_uuid = client_uuid
        sub.sub_token = sub_token

        # Синхронизируем новые параметры с 3X-UI панелью
        if sub.is_active:
            try:
                from services.xui_service import ThreeXUIService
                xui = ThreeXUIService(
                    xui_url=config.xui_url,
                    username=config.xui_username,
                    password=config.xui_password,
                    inbound_id=config.xui_inbound_id,
                )
                email = f"id_{sub.user_id}"
                await xui.sync_client(client_uuid, email, sub_token, sub.expires_at)
                logger.info("Sub token %s: synced new config to 3X-UI", token)
            except Exception as exc:
                logger.exception("Failed to sync updated client %d to 3X-UI: %s", sub.user_id, exc)

    if not sub.vless_link:
        raise HTTPException(status_code=404, detail="Config not generated")

    # Принудительно подставляем имя сервера как фрагмент (#) VLESS-ссылки.
    # Срезаем существующий фрагмент (если есть) и всегда добавляем display_name.
    import urllib.parse
    server_display_name = urllib.parse.quote(config.primary_server.display_name)
    vless_link = sub.vless_link.split("#", 1)[0] + "#" + server_display_name

    content = vless_link + "\n"
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    # ── Получение статистики использования трафика (3X-UI) ───────────────────
    upload = 0
    download = 0
    total = 0
    expire = 0
    if sub.expires_at:
        expire = int(sub.expires_at.timestamp())

    try:
        from services.xui_service import ThreeXUIService
        xui = ThreeXUIService(
            xui_url=config.xui_url,
            username=config.xui_username,
            password=config.xui_password,
            inbound_id=config.xui_inbound_id,
        )
        email = f"id_{sub.user_id}"
        traffic = await xui.get_client_traffic(email)
        if traffic:
            upload = traffic.get("up", 0)
            download = traffic.get("down", 0)
            total = traffic.get("total", 0)
    except Exception as exc:
        logger.warning(
            "Failed to fetch traffic stats for client %d: %s",
            sub.user_id, exc
        )

    headers = {
        "profile-title": "💎 EDELIA | VPN".encode("utf-8").decode("latin-1"),
        "Content-Disposition": (
            'attachment; filename="EDELIA | VPN"; '
            "filename*=utf-8''EDELIA%20%7C%20VPN"
        ),
        "profile-update-interval": "24",
        "subscription-userinfo": f"upload={upload}; download={download}; total={total}; expire={expire}",
    }

    return Response(
        content=encoded_content,
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )
