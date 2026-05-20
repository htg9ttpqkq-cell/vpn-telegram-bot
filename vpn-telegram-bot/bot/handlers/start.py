"""Стартовые хендлеры и главное меню (модуль; точка входа — `bot.py`)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Прямой запуск `python bot/handlers/start.py` не добавляет корень репо в sys.path.
if __name__ == "__main__" and __package__ is None:
    _repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_repo_root))

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.handlers import ui_texts
from bot.handlers.callback_tools import edit_callback_message
from bot.handlers.i18n import all_locale_values, normalize_lang, plan_title, t
from bot.middlewares.tidy_chat import TidyChatMiddleware
from core.config import Config
from core.database import Database
from services.subscription_service import SubscriptionService
from services.user_service import UserService

router = Router()
router.message.middleware(TidyChatMiddleware())

_APP_LABELS = {
    "happ": "Happ (iOS/Android)",
    "hiddify": "Hiddify",
    "v2rayng": "v2rayNG (Android)",
    "nekoray": "Nekoray (PC)",
}


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t(lang, "btn_install"))
    builder.button(text=t(lang, "btn_profile"))
    builder.button(text=t(lang, "btn_tariffs"))
    builder.button(text=t(lang, "btn_invite"))
    builder.button(text=t(lang, "btn_faq"))
    builder.button(
        text=t(lang, "btn_switch_en") if lang != "en" else t(lang, "btn_switch_ru")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def _menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    return builder.as_markup()


def dashboard_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Inline actions for edited messages (Telegram forbids reply keyboards here)."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_install"), callback_data="install_vpn")
    builder.button(text=t(lang, "btn_profile"), callback_data="my_subscription")
    builder.row()
    builder.button(text=t(lang, "btn_tariffs"), callback_data="buy_subscription")
    builder.button(text=t(lang, "btn_invite"), callback_data="invite_friend")
    builder.row()
    builder.button(text=t(lang, "btn_faq"), callback_data="faq")
    builder.button(
        text=t(lang, "btn_switch_en") if lang != "en" else t(lang, "btn_switch_ru"),
        callback_data="switch_language",
    )
    builder.adjust(2)
    return builder.as_markup()


def _install_apps_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slug, label in _APP_LABELS.items():
        builder.button(text=label, callback_data=f"install_app:{slug}")
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def _dashboard_text(subscription, lang: str) -> str:
    now = datetime.now(timezone.utc)
    is_active = bool(
        subscription
        and subscription.is_active
        and subscription.expires_at
        and subscription.expires_at > now
    )
    status = t(lang, "status_active") if is_active else t(lang, "status_inactive")
    return f"{t(lang, 'home_title')}\n\n{t(lang, 'status_label')}:\n{status}"


@router.message(CommandStart())
async def start(message: Message, db: Database, config: Config) -> None:
    if message.from_user is None:
        return
    user_id = message.from_user.id
    user_svc = UserService(db)
    user_svc.get_or_create_user(user_id)
    granted = SubscriptionService(db, config).try_grant_welcome_trial(user_id)
    lang = user_svc.get_language(user_id)
    subscription = db.get_subscription(user_id)
    extra = f"\n\n{t(lang, 'trial_granted_notice')}" if granted else ""
    await message.answer(
        _dashboard_text(subscription, lang) + extra,
        reply_markup=main_menu_keyboard(lang),
    )


@router.callback_query(F.data == "menu")
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, db: Database) -> None:
    subscription = None
    lang = "ru"
    if callback.from_user is not None:
        user_id = callback.from_user.id
        subscription = db.get_subscription(user_id)
        lang = UserService(db).get_language(user_id)
    await edit_callback_message(
        callback,
        _dashboard_text(subscription, lang),
        reply_markup=dashboard_inline_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "support")
async def support(callback: CallbackQuery, config: Config, db: Database) -> None:
    lang = (
        UserService(db).get_language(callback.from_user.id)
        if callback.from_user
        else "ru"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    await edit_callback_message(
        callback,
        f"{t(lang, 'support_title')}\n\n{config.support_text}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "switch_language")
async def switch_language(callback: CallbackQuery, db: Database) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    user_svc = UserService(db)
    current = user_svc.get_language(user_id)
    new_lang = "en" if current != "en" else "ru"
    db.set_user_language(user_id, new_lang)
    subscription = db.get_subscription(user_id)
    await edit_callback_message(
        callback,
        _dashboard_text(subscription, new_lang),
        reply_markup=dashboard_inline_keyboard(new_lang),
    )
    await callback.answer()


@router.callback_query(F.data == "install_vpn")
async def install_vpn(callback: CallbackQuery, db: Database) -> None:
    lang = (
        UserService(db).get_language(callback.from_user.id)
        if callback.from_user
        else "ru"
    )
    await edit_callback_message(
        callback,
        t(lang, "install_title"),
        reply_markup=_install_apps_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "setup_guide")
async def setup_guide(callback: CallbackQuery, db: Database) -> None:
    await install_vpn(callback, db)


@router.callback_query(F.data.startswith("install_app:"))
async def install_app(callback: CallbackQuery, db: Database) -> None:
    lang = (
        UserService(db).get_language(callback.from_user.id)
        if callback.from_user
        else "ru"
    )
    app = callback.data.split(":", maxsplit=1)[1]
    app_name = _APP_LABELS.get(app, "App")
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_get_config"), callback_data="get_config")
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    builder.adjust(1)
    await edit_callback_message(
        callback,
        f"{app_name}\n\n{t(lang, 'install_steps')}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "invite_friend")
async def invite_friend(callback: CallbackQuery, db: Database) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    lang = UserService(db).get_language(callback.from_user.id)
    me = await callback.bot.get_me()
    username = me.username or "bot"
    link = f"https://t.me/{username}?start={callback.from_user.id}"
    await edit_callback_message(
        callback,
        f"{t(lang, 'invite_title')}\n\n{t(lang, 'invite_link_label')}\n{link}\n\n"
        f"{t(lang, 'invite_reward')}",
        reply_markup=_menu_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "faq")
async def faq(callback: CallbackQuery, db: Database) -> None:
    lang = (
        UserService(db).get_language(callback.from_user.id)
        if callback.from_user
        else "ru"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_support"), callback_data="support")
    builder.button(text=t(lang, "btn_back"), callback_data="menu")
    builder.adjust(1)
    await edit_callback_message(
        callback,
        f"{t(lang, 'faq_title')}\n\n{t(lang, 'faq_body')}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


# --- Reply keyboard (same actions as inline dashboard; text matches both locales) ---


@router.message(F.text.in_(all_locale_values("btn_install")))
async def msg_install(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    lang = UserService(db).get_language(message.from_user.id)
    await message.answer(
        t(lang, "install_title"),
        reply_markup=_install_apps_keyboard(lang),
    )


@router.message(F.text.in_(all_locale_values("btn_profile")))
async def msg_profile(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    lang = UserService(db).get_language(user_id)
    subscription = db.get_subscription(user_id)
    now = datetime.now(timezone.utc)
    is_active = bool(
        subscription
        and subscription.is_active
        and subscription.expires_at
        and subscription.expires_at > now
    )
    status = t(lang, "profile_active") if is_active else t(lang, "profile_inactive")
    plan_label = (
        plan_title(lang, subscription.plan or "")
        if subscription
        else "—"
    )
    end_date = (
        subscription.expires_at.strftime("%Y-%m-%d")
        if subscription and subscription.expires_at
        else "—"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_renew"), callback_data="buy_subscription")
    builder.button(text=t(lang, "btn_usage"), callback_data="usage")
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    builder.adjust(1)
    await message.answer(
        f"{t(lang, 'profile_title')}\n\n"
        f"{t(lang, 'profile_status')}: {status}\n"
        f"{t(lang, 'profile_plan')}: {plan_label}\n"
        f"{t(lang, 'profile_expiry')}: {end_date}",
        reply_markup=builder.as_markup(),
    )


@router.message(F.text.in_(all_locale_values("btn_tariffs")))
async def msg_tariffs(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    user_svc = UserService(db)
    user_svc.get_or_create_user(user_id)
    lang = user_svc.get_language(user_id)
    builder = InlineKeyboardBuilder()
    for code, label in ui_texts.plan_titles[normalize_lang(lang)].items():
        builder.button(text=label, callback_data=f"plan:{code}")
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    builder.adjust(1)
    await message.answer(
        t(lang, "choose_plan"),
        reply_markup=builder.as_markup(),
    )


@router.message(F.text.in_(all_locale_values("btn_invite")))
async def msg_invite(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    lang = UserService(db).get_language(message.from_user.id)
    me = await message.bot.get_me()
    username = me.username or "bot"
    link = f"https://t.me/{username}?start={message.from_user.id}"
    await message.answer(
        f"{t(lang, 'invite_title')}\n\n{t(lang, 'invite_link_label')}\n{link}\n\n"
        f"{t(lang, 'invite_reward')}",
        reply_markup=main_menu_keyboard(lang),
    )


@router.message(F.text.in_(all_locale_values("btn_faq")))
async def msg_faq(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    lang = UserService(db).get_language(message.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_support"), callback_data="support")
    builder.button(text=t(lang, "btn_back"), callback_data="menu")
    builder.adjust(1)
    await message.answer(
        f"{t(lang, 'faq_title')}\n\n{t(lang, 'faq_body')}",
        reply_markup=builder.as_markup(),
    )


@router.message(F.text.in_(all_locale_values("btn_switch_en")))
async def msg_english(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    db.set_user_language(user_id, "en")
    subscription = db.get_subscription(user_id)
    await message.answer(
        _dashboard_text(subscription, "en"),
        reply_markup=main_menu_keyboard("en"),
    )


@router.message(F.text.in_(all_locale_values("btn_switch_ru")))
async def msg_russian(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    user_id = message.from_user.id
    db.set_user_language(user_id, "ru")
    subscription = db.get_subscription(user_id)
    await message.answer(
        _dashboard_text(subscription, "ru"),
        reply_markup=main_menu_keyboard("ru"),
    )


if __name__ == "__main__":
    raise SystemExit(
        "Этот файл — только модуль хендлеров, его не запускают отдельно.\n"
        "Из корня репозитория выполните:\n"
        "  python bot.py\n"
    )