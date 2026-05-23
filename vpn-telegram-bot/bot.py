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
from services.yookassa_service import YooKassaService


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

    # Защита от флуда / быстрых нажатий
    rate_limit = RateLimitMiddleware()
    dp.message.middleware(rate_limit)
    dp.callback_query.middleware(rate_limit)

    # Uvicorn: host/port читаются из config (→ UVICORN_HOST / UVICORN_PORT в .env)
    # Default: 127.0.0.1:8000 — безопасно за Nginx-прокси.
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
            "Starting bot polling and FastAPI web server on %s:%d ...",
            config.uvicorn_host,
            config.uvicorn_port,
        )
        # asyncio.gather — параллельный запуск, ни один не блокирует другой
        await asyncio.gather(
            dp.start_polling(bot),
            server.serve(),
        )
    except TelegramNetworkError as exc:
        log.error(
            "Telegram API request failed (network/timeout): %s. "
            "From this host, HTTPS to api.telegram.org must work (check VPN, firewall, DNS, "
            "or regional blocking). Try: curl -I --connect-timeout 10 https://api.telegram.org",
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
