from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callback_tools import edit_callback_message
from .i18n import plan_title, t
from core.config import Config, PLAN_PRICES_RUB
from core.database import Database
from services.platega_service import PlategaService
from services.user_service import UserService

router = Router()


def _menu_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    return builder.as_markup()


def plan_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    for code in ("1m", "3m", "12m"):
        builder.button(text=plan_title(lang, code), callback_data=f"plan:{code}")
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "buy_subscription")
async def buy_subscription(callback: CallbackQuery, db: Database) -> None:
    lang = (
        UserService(db).get_language(callback.from_user.id)
        if callback.from_user
        else "ru"
    )
    await edit_callback_message(
        callback,
        t(lang, "choose_plan"),
        reply_markup=plan_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("plan:"))
async def handle_plan_selection(
    callback: CallbackQuery,
    db: Database,
    config: Config,
) -> None:
    if callback.from_user is None:
        await callback.answer("User not found", show_alert=True)
        return
    lang = UserService(db).get_language(callback.from_user.id)

    plan_code = callback.data.split(":", maxsplit=1)[1]
    amount = PLAN_PRICES_RUB.get(plan_code)
    if amount is None:
        await callback.answer(t(lang, "unknown_plan"), show_alert=True)
        return

    user_id = callback.from_user.id
    db.upsert_user(user_id)
    plan_name = plan_title(lang, plan_code)

    try:
        platega = PlategaService(
            merchant_id=config.platega_merchant_id,
            secret_key=config.platega_secret_key,
            return_url=config.platega_return_url,
        )
        payload_str = f"user_id:{user_id};plan:{plan_code}"
        result = await platega.create_payment(
            amount_rub=float(amount),
            description=f"EDELIA VPN — {plan_name}",
            payload=payload_str,
        )

        # Реальный ответ: {"transactionId": "...", "url": "...", ...}
        payment_url = result.get("url") or result.get("redirect")
        transaction_id = str(result.get("transactionId", ""))

        if not payment_url or not transaction_id:
            raise ValueError("Platega вернул пустой URL или ID транзакции")

        # Сохраняем запись платежа в БД
        db.create_payment(
            user_id=user_id,
            plan=plan_code,
            amount=amount,
            status="pending",
            platega_transaction_id=transaction_id,
            comment=f"VPN_{user_id}_{plan_code}",
        )

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="💳 Оплатить онлайн",
            url=payment_url,
        ))
        builder.row(InlineKeyboardButton(
            text=t(lang, "btn_menu"),
            callback_data="menu",
        ))

        await edit_callback_message(
            callback,
            f"{t(lang, 'checkout')}\n\n"
            f"{t(lang, 'profile_plan')}: <b>{plan_name}</b>\n"
            f"{t(lang, 'price')}: <b>{amount} ₽</b>\n\n"
            "Нажмите кнопку ниже для безопасной онлайн-оплаты:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )

    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(
            "Platega payment creation failed for user %d: %s", user_id, exc
        )
        builder = InlineKeyboardBuilder()
        builder.button(text=t(lang, "btn_menu"), callback_data="menu")
        await edit_callback_message(
            callback,
            "⚠️ Не удалось создать ссылку на оплату. Попробуйте позже или обратитесь в поддержку.",
            reply_markup=builder.as_markup(),
        )

    await callback.answer()
