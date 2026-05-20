from datetime import datetime, timedelta, timezone
from html import escape

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callback_tools import edit_callback_message
from core.config import Config
from core.database import Database
from services.subscription_service import SubscriptionService
from services.payment_service import PaymentService
from services.vpn_provision import vless_config_link

router = Router()


class AdminStates(StatesGroup):
    waiting_activate_user_id = State()
    waiting_reset_user_id = State()
    waiting_clear_subscription_user_id = State()


def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Pending payments", callback_data="admin:pending")
    builder.button(text="Список пользователей", callback_data="admin:list")
    builder.button(text="Активировать подписку", callback_data="admin:activate")
    builder.button(text="Удалить подписку", callback_data="admin:clear_subscription")
    builder.button(text="Сбросить конфиг", callback_data="admin:reset")
    builder.button(text="Закрыть", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def _is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admin_ids


@router.message(Command("admin"))
async def admin_panel(message: Message, config: Config) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id, config):
        await message.answer("Нет доступа.")
        return
    await message.answer("Админ-панель:", reply_markup=admin_keyboard())


@router.callback_query(F.data.startswith("admin:"))
async def admin_actions(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
    config: Config,
) -> None:
    if callback.from_user is None or not _is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return

    action = callback.data.split(":", maxsplit=1)[1]
    if action == "list":
        users = db.list_users(limit=50)
        if not users:
            text = "Пользователей пока нет."
        else:
            lines = []
            for user in users:
                end_date = user.expires_at.strftime("%Y-%m-%d") if user.expires_at else "—"
                status = "active" if user.is_active else "inactive"
                plan = user.plan or "-"
                lines.append(f"{user.user_id} | {status} | {plan} | {end_date}")
            text = "Последние пользователи:\n" + "\n".join(lines)
        await edit_callback_message(callback, text, reply_markup=admin_keyboard())
        await callback.answer()
        return

    if action == "pending":
        pending = db.list_pending_payments(limit=20)
        if not pending:
            await edit_callback_message(
                callback,
                "Нет платежей в pending_review.",
                reply_markup=admin_keyboard(),
            )
            await callback.answer()
            return

        lines = [
            f"#{p.id} | u:{p.user_id} | {p.plan} | {p.amount} RUB | {p.comment or '-'}"
            for p in pending
        ]
        await edit_callback_message(
            callback,
            "Ожидают подтверждения:\n" + "\n".join(lines),
            reply_markup=admin_keyboard(),
        )
        await callback.answer()
        return

    if action == "activate":
        await state.set_state(AdminStates.waiting_activate_user_id)
        await edit_callback_message(
            callback,
            "Введите user_id для активации на 30 дней:",
            reply_markup=admin_keyboard(),
        )
        await callback.answer()
        return

    if action == "clear_subscription":
        await state.set_state(AdminStates.waiting_clear_subscription_user_id)
        await edit_callback_message(
            callback,
            "Введите user_id для удаления подписки (доступ и конфиг будут сброшены):",
            reply_markup=admin_keyboard(),
        )
        await callback.answer()
        return

    if action == "reset":
        await state.set_state(AdminStates.waiting_reset_user_id)
        await edit_callback_message(
            callback,
            "Введите user_id для сброса конфига:",
            reply_markup=admin_keyboard(),
        )
        await callback.answer()
        return

    await callback.answer("Неизвестное действие", show_alert=True)


@router.callback_query(F.data.startswith("adminpay:"))
async def admin_payment_actions(
    callback: CallbackQuery,
    db: Database,
    config: Config,
) -> None:
    if callback.from_user is None or not _is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, action, raw_payment_id = callback.data.split(":", maxsplit=2)
    if not raw_payment_id.isdigit():
        await callback.answer("Некорректный ID", show_alert=True)
        return
    payment_id = int(raw_payment_id)
    payment = db.get_payment_by_id(payment_id)
    if payment is None:
        await callback.answer("Платеж не найден", show_alert=True)
        return
    if payment.status != "pending_review":
        await callback.answer("Уже обработан", show_alert=True)
        return

    if action == "reject":
        payment_service = PaymentService(db, config)
        payment_service.reject_payment(payment_id)
        await callback.bot.send_message(
            payment.user_id,
            "Платеж отклонен. Проверьте перевод и попробуйте снова.",
        )
        await edit_callback_message(
            callback,
            f"Payment #{payment_id} отклонен.",
            reply_markup=admin_keyboard(),
        )
        await callback.answer("Rejected")
        return

    if action == "confirm":
        payment_service = PaymentService(db, config)
        activation = payment_service.confirm_payment(payment_id)
        await payment_service.notify_user_about_activation(payment.user_id, activation)
        await edit_callback_message(
            callback,
            f"Payment #{payment_id} подтвержден, подписка активирована.",
            reply_markup=admin_keyboard(),
        )
        await callback.answer("Confirmed")
        return

    await callback.answer("Неизвестное действие", show_alert=True)


@router.message(AdminStates.waiting_activate_user_id)
async def admin_activate_user(
    message: Message,
    state: FSMContext,
    db: Database,
    config: Config,
) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id, config):
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Нужен числовой user_id.")
        return

    target_user_id = int(message.text)
    db.upsert_user(target_user_id)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    db.set_subscription(
        target_user_id,
        plan="1m",
        expires_at=expires_at,
        is_active=True,
        vless_link=vless_config_link(config),
    )
    db.set_trial_consumed(target_user_id)

    await state.clear()
    await message.answer(
        f"Подписка активирована для {target_user_id} до {expires_at.strftime('%Y-%m-%d %H:%M UTC')}.",
        reply_markup=admin_keyboard(),
    )


@router.message(AdminStates.waiting_clear_subscription_user_id)
async def admin_clear_subscription(
    message: Message,
    state: FSMContext,
    db: Database,
    config: Config,
) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id, config):
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Нужен числовой user_id.")
        return

    target_user_id = int(message.text)
    db.upsert_user(target_user_id)
    db.clear_subscription(target_user_id)

    await state.clear()
    await message.answer(
        f"Подписка удалена для user_id {target_user_id}.",
        reply_markup=admin_keyboard(),
    )


@router.message(AdminStates.waiting_reset_user_id)
async def admin_reset_config(
    message: Message,
    state: FSMContext,
    db: Database,
    config: Config,
) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id, config):
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Нужен числовой user_id.")
        return

    target_user_id = int(message.text)
    db.upsert_user(target_user_id)
    new_link = vless_config_link(config)
    db.reset_vless_link(target_user_id, new_link)

    await state.clear()
    safe_link = escape(new_link, quote=True)
    await message.answer(
        f"Конфиг сброшен для {target_user_id}:\n<code>{safe_link}</code>",
        reply_markup=admin_keyboard(),
        parse_mode=ParseMode.HTML,
    )
