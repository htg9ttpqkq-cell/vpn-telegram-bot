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
        logging.getLogger(__name__).info("YooKassa: enabled")
    else:
        logging.getLogger(__name__).info("YooKassa: disabled (set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY to enable)")

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

    log = logging.getLogger(__name__)
    
    # Конфигурация веб-сервера Uvicorn
    config_uvicorn = uvicorn.Config(
        "web.webhook:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config_uvicorn)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        log.info("Starting bot polling and FastAPI web server concurrently...")
        await asyncio.gather(
            dp.start_polling(bot),
            server.serve()
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
