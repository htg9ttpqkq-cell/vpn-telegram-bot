"""Точка входа: параллельный запуск Aiogram polling + Uvicorn FastAPI
и фоновый планировщик автоматического отключения просроченных подписок.

Планировщик запускается каждые EXPIRY_CHECK_INTERVAL_SEC секунд и:
  1. Находит все активные подписки с истёкшим expires_at.
  2. Деактивирует их в локальной БД.
  3. Вызывает XUI disable_client (enable=False) — клиент остаётся в панели.
  4. Отправляет вежливое брендированное уведомление пользователю в Telegram.
"""

import asyncio
import logging

import uvicorn

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError

from core.config import load_config
from bot.handlers import admin, payment, profile, start
from bot.middlewares.rate_limit import RateLimitMiddleware
from core.database import Database
from services.subscription_service import SubscriptionService
from services.yookassa_service import YooKassaService

# Интервал проверки просроченных подписок (секунды). 1800 = 30 минут.
EXPIRY_CHECK_INTERVAL_SEC = 1800


async def expiry_checker_loop(
    db: Database,
    config,
    bot: Bot,
) -> None:
    """Фоновый цикл: каждые EXPIRY_CHECK_INTERVAL_SEC секунд проверяет и
    деактивирует просроченные подписки.

    Запускается как отдельная asyncio-задача в asyncio.gather() вместе
    с polling и uvicorn, поэтому не блокирует основной event loop.
    """
    log = logging.getLogger(__name__ + ".expiry_checker")
    subscription_svc = SubscriptionService(db, config)

    log.info("Expiry checker started (interval=%ds)", EXPIRY_CHECK_INTERVAL_SEC)

    while True:
        try:
            expired = db.get_expired_active_subscriptions()
            if expired:
                log.info("Expiry check: found %d expired subscription(s)", len(expired))
                for sub in expired:
                    await subscription_svc.expire_and_disable(sub, bot)
            else:
                log.debug("Expiry check: no expired subscriptions")
        except Exception:
            log.exception("Expiry checker encountered an unexpected error — continuing")

        # Ждём следующий цикл. asyncio.sleep не блокирует event loop.
        await asyncio.sleep(EXPIRY_CHECK_INTERVAL_SEC)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger(__name__)

    config = load_config()
    db = Database(config.db_path)
    db.init()

    yookassa = None
    if config.yookassa_enabled:
        yookassa = YooKassaService(
            shop_id=config.yookassa_shop_id,
            secret_key=config.yookassa_secret_key,
            return_url=config.yookassa_return_url,
        )
        log.info("YooKassa: enabled")
    else:
        log.info(
            "YooKassa: disabled (set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY to enable)"
        )

    # Выводим список серверов при старте для диагностики
    for i, srv in enumerate(config.servers, 1):
        log.info(
            "Server #%d: %s | XUI=%s | inbound=%d",
            i, srv.display_name, srv.xui_url, srv.xui_inbound_id,
        )

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(db=db, config=config, yookassa=yookassa)

    dp.include_router(start.router)
    dp.include_router(payment.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)

    # Защита от флуда
    rate_limit = RateLimitMiddleware()
    dp.message.middleware(rate_limit)
    dp.callback_query.middleware(rate_limit)

    # Uvicorn: host/port из config (→ UVICORN_HOST / UVICORN_PORT в .env)
    uvicorn_cfg = uvicorn.Config(
        "web.webhook:app",
        host=config.uvicorn_host,
        port=config.uvicorn_port,
        log_level="info",
    )
    server = uvicorn.Server(uvicorn_cfg)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        log.info(
            "Starting: polling + web server (%s:%d) + expiry checker ...",
            config.uvicorn_host,
            config.uvicorn_port,
        )
        # Три задачи запускаются параллельно:
        # 1. Telegram polling (aiogram)
        # 2. FastAPI веб-сервер (uvicorn)
        # 3. Фоновый планировщик отключения просроченных подписок
        await asyncio.gather(
            dp.start_polling(bot),
            server.serve(),
            expiry_checker_loop(db, config, bot),
        )
    except TelegramNetworkError as exc:
        log.error(
            "Telegram API request failed (network/timeout): %s. "
            "Check VPN/firewall/DNS. Try: curl -I --connect-timeout 10 https://api.telegram.org",
            exc,
        )
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
