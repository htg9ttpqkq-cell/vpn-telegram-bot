from datetime import datetime, timezone
from html import escape

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import secrets
import uuid
from .callback_tools import edit_callback_message
from .i18n import plan_title, t
from core.config import Config
from core.database import Database
from services.user_service import UserService
from services.vpn_provision import generate_vless_link, needs_config_refresh, vless_config_link

router = Router()


def _menu_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    return builder.as_markup()


@router.callback_query(F.data == "my_subscription")
async def my_subscription(callback: CallbackQuery, db: Database) -> None:
    if callback.from_user is None:
        await callback.answer("User not found", show_alert=True)
        return

    user_id = callback.from_user.id
    UserService(db).get_or_create_user(user_id)
    lang = UserService(db).get_language(user_id)
    subscription = db.get_subscription(user_id)

    now = datetime.now(timezone.utc)
    is_active = bool(
        subscription
        and subscription.is_active
        and subscription.expires_at is not None
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

    await edit_callback_message(
        callback,
        f"{t(lang, 'profile_title')}\n\n"
        f"{t(lang, 'profile_status')}: {status}\n"
        f"{t(lang, 'profile_plan')}: {plan_label}\n"
        f"{t(lang, 'profile_expiry')}: {end_date}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "usage")
async def usage(callback: CallbackQuery, db: Database) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    user_id = callback.from_user.id
    lang = UserService(db).get_language(user_id)
    subscription = db.get_subscription(user_id)
    now = datetime.now(timezone.utc)

    # Статистика подписки
    if subscription and subscription.plan and subscription.expires_at:
        from .i18n import plan_title as _plan_title
        plan_label = _plan_title(lang, subscription.plan)
        exp_str = subscription.expires_at.strftime("%Y-%m-%d")
        days_left = max(0, (subscription.expires_at - now).days)
    else:
        plan_label = "—"
        exp_str = "—"
        days_left = 0

    # Реферальная статистика
    total_invited, bonuses_received = db.get_referral_stats(user_id)

    if lang == "ru":
        msg = (
            f"<b>{t(lang, 'stats_title')}</b>\n\n"
            f"📋 <b>{t(lang, 'stats_plan')}:</b> {plan_label}\n"
            f"📅 <b>{t(lang, 'stats_expires')}:</b> {exp_str}\n"
            f"⏳ <b>{t(lang, 'stats_days_left')}:</b> {days_left}\n\n"
            f"👥 <b>{t(lang, 'stats_invited')}:</b> {total_invited}\n"
            f"🎁 <b>{t(lang, 'stats_bonuses')}:</b> {bonuses_received}"
        )
    else:
        msg = (
            f"<b>{t(lang, 'stats_title')}</b>\n\n"
            f"📋 <b>{t(lang, 'stats_plan')}:</b> {plan_label}\n"
            f"📅 <b>{t(lang, 'stats_expires')}:</b> {exp_str}\n"
            f"⏳ <b>{t(lang, 'stats_days_left')}:</b> {days_left}\n\n"
            f"👥 <b>{t(lang, 'stats_invited')}:</b> {total_invited}\n"
            f"🎁 <b>{t(lang, 'stats_bonuses')}:</b> {bonuses_received}"
        )

    await edit_callback_message(
        callback,
        msg,
        reply_markup=_menu_keyboard(lang),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@router.callback_query(F.data == "get_config")
async def get_config(callback: CallbackQuery, db: Database, config: Config) -> None:
    if callback.from_user is None:
        await callback.answer("User not found", show_alert=True)
        return

    lang = UserService(db).get_language(callback.from_user.id)
    subscription = db.get_subscription(callback.from_user.id)
    now = datetime.now(timezone.utc)
    if (
        subscription is None
        or not subscription.is_active
        or subscription.expires_at is None
        or subscription.expires_at <= now
    ):
        builder = InlineKeyboardBuilder()
        builder.button(text=t(lang, "btn_tariffs"), callback_data="buy_subscription")
        builder.button(text=t(lang, "btn_menu"), callback_data="menu")
        builder.adjust(1)
        await edit_callback_message(
            callback,
            t(lang, "not_active"),
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        return

    # Если требуется обновить VLESS-шаблон или сгенерировать недостающие токены
    if (
        needs_config_refresh(subscription, config)
        or not subscription.sub_token
        or not subscription.client_uuid
    ):
        sub_token = subscription.sub_token or secrets.token_urlsafe(16)
        client_uuid = subscription.client_uuid or str(uuid.uuid4())
        vless_link = generate_vless_link(config.vless_template, client_uuid)

        db.set_subscription(
            callback.from_user.id,
            plan=subscription.plan or "trial",
            expires_at=subscription.expires_at,
            is_active=True,
            vless_link=vless_link,
            sub_token=sub_token,
            client_uuid=client_uuid,
        )
        # Перезагружаем подписку из БД
        subscription = db.get_subscription(callback.from_user.id)

    vless_link = subscription.vless_link or ""
    sub_url = f"{config.subscription_config_base_url}/sub/{subscription.sub_token}"

    if lang == "ru":
        msg = (
            f"<b>{t(lang, 'config_title')}</b>\n\n"
            f"1️⃣ <b>Ссылка для ручного импорта</b> (скопируйте её и импортируйте в VPN-клиент):\n"
            f"<code>{escape(vless_link)}</code>\n\n"
            f"2️⃣ <b>Ссылка автообновления подписки</b> (для Shadowrocket, Nekobox, v2rayN):\n"
            f"<code>{escape(sub_url)}</code>\n\n"
            f"<i>Рекомендуется использовать ссылку автообновления, чтобы ваш клиент автоматически узнавал о продлении подписки.</i>"
        )
    else:
        msg = (
            f"<b>{t(lang, 'config_title')}</b>\n\n"
            f"1️⃣ <b>Manual import link</b> (copy and import into your VPN client):\n"
            f"<code>{escape(vless_link)}</code>\n\n"
            f"2️⃣ <b>Auto-update subscription link</b> (for Shadowrocket, Nekobox, v2rayN):\n"
            f"<code>{escape(sub_url)}</code>\n\n"
            f"<i>It is recommended to use the subscription link so your client automatically detects renewals.</i>"
        )

    await edit_callback_message(
        callback,
        msg,
        reply_markup=_menu_keyboard(lang),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()
