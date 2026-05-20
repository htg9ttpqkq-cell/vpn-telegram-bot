import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError

from core.config import load_config
from bot.handlers import admin, payment, profile, start
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

    log = logging.getLogger(__name__)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
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
