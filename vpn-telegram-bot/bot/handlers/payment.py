from datetime import datetime, timezone
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


def plan_keyboard(lang: str, db: Database, user_id: int):
    builder = InlineKeyboardBuilder()
    plans_to_show = []
    if not db.user_trial_consumed(user_id):
        plans_to_show.append("trial")
    plans_to_show.extend(["1m", "3m", "12m"])
    
    for code in plans_to_show:
        builder.button(text=plan_title(lang, code), callback_data=f"plan:{code}")
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "buy_subscription")
async def buy_subscription(callback: CallbackQuery, db: Database) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    lang = UserService(db).get_language(user_id)
    await edit_callback_message(
        callback,
        t(lang, "choose_plan"),
        reply_markup=plan_keyboard(lang, db, user_id),
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
    if plan_code == "trial":
        user_id = callback.from_user.id
        subscription = db.get_subscription(user_id)
        now = datetime.now(timezone.utc)
        if subscription and subscription.is_active and subscription.expires_at and subscription.expires_at > now:
            await callback.answer(
                "У вас уже есть активная подписка." if lang == "ru" else "You already have an active subscription.",
                show_alert=True,
            )
            return

        if db.user_trial_consumed(user_id):
            await callback.answer(
                "Вы уже использовали пробный период." if lang == "ru" else "You have already used the trial period.",
                show_alert=True,
            )
            return

        from services.subscription_service import SubscriptionService
        sub_svc = SubscriptionService(db, config)
        granted = await sub_svc.try_grant_welcome_trial(user_id)
        if granted:
            builder = InlineKeyboardBuilder()
            builder.button(text=t(lang, "btn_get_config"), callback_data="get_config")
            builder.button(text=t(lang, "btn_menu"), callback_data="menu")
            builder.adjust(1)
            await edit_callback_message(
                callback,
                "💎 <b>Пробный период активирован!</b>\n\n"
                "Вам предоставлено 7 дней бесплатного премиум-доступа. Нажмите кнопку ниже, чтобы получить ссылку для подключения:"
                if lang == "ru"
                else "💎 <b>Trial period activated!</b>\n\n"
                "You have been granted 7 days of free premium access. Tap the button below to get your connection link:",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        else:
            await callback.answer(
                "Не удалось активировать пробный период." if lang == "ru" else "Failed to activate trial period.",
                show_alert=True,
            )
        return

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
