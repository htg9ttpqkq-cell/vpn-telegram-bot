from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callback_tools import edit_callback_message
from .i18n import plan_title, t
from core.config import Config, PLAN_PRICES_RUB
from core.database import Database
from services.payment_service import PaymentService
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
    payment_comment = f"VPN_{user_id}_{plan_code}"
    plan_name = plan_title(lang, plan_code)

    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_pay"), callback_data=f"manual_paid:{plan_code}")
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    builder.adjust(1)

    await edit_callback_message(
        callback,
        f"{t(lang, 'checkout')}\n\n"
        f"{t(lang, 'profile_plan')}: <b>{plan_name}</b>\n"
        f"{t(lang, 'price')}: <b>{amount} ₽</b>\n\n"
        f"{t(lang, 'secure_sbp')}\n"
        f"<code>{config.sbp_phone_or_card}</code>\n"
        f"{config.sbp_recipient}\n\n"
        f"Комментарий: <code>{payment_comment}</code>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("manual_paid:"))
async def manual_paid(
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
    comment = f"VPN_{user_id}_{plan_code}"
    payment_service = PaymentService(db, config)
    payment_id = payment_service.create_payment(
        user_id=user_id,
        plan=plan_code,
        amount=amount,
        comment=comment,
    )

    for admin_id in config.admin_ids:
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="Confirm", callback_data=f"adminpay:confirm:{payment_id}")
            builder.button(text="Reject", callback_data=f"adminpay:reject:{payment_id}")
            builder.adjust(2)
            await callback.bot.send_message(
                admin_id,
                (
                    "Новая заявка на ручную проверку СБП\n"
                    f"Payment ID: {payment_id}\n"
                    f"user_id: {user_id}\n"
                    f"plan: {plan_code}\n"
                    f"amount: {amount} RUB\n"
                    f"comment: {comment}"
                ),
                reply_markup=builder.as_markup(),
            )
        except Exception:
            continue

    await edit_callback_message(
        callback,
        t(lang, "payment_pending"),
        reply_markup=_menu_keyboard(lang),
    )
    await callback.answer()
