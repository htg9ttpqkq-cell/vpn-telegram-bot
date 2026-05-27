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
async def my_subscription(callback: CallbackQuery, db: Database, config: Config) -> None:
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

    sub_link_str = ""
    if subscription and subscription.sub_token:
        sub_url = f"{config.subscription_config_base_url}/sub/{subscription.sub_token}"
        if lang == "ru":
            sub_link_str = f"\n\n🔗 <b>Ссылка подписки:</b>\n<code>{sub_url}</code>"
        else:
            sub_link_str = f"\n\n🔗 <b>Subscription link:</b>\n<code>{sub_url}</code>"

    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_renew"), callback_data="buy_subscription")
    builder.button(text=t(lang, "btn_usage"), callback_data="usage")
    builder.button(text=t(lang, "btn_menu"), callback_data="menu")
    builder.adjust(1)

    await edit_callback_message(
        callback,
        f"{t(lang, 'profile_title')}\n\n"
        f"👤 ID: <code>{user_id}</code>\n"
        f"{t(lang, 'profile_status')}: {status}\n"
        f"{t(lang, 'profile_plan')}: {plan_label}\n"
        f"{t(lang, 'profile_expiry')}: <code>{end_date}</code>"
        f"{sub_link_str}",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML,
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
            f"{t(lang, 'stats_title')}\n\n"
            f"📅 <b>{t(lang, 'stats_plan')}:</b> {plan_label}\n"
            f"📍 <b>{t(lang, 'stats_expires')}:</b> {exp_str}\n"
            f"✨ <b>{t(lang, 'stats_days_left')}:</b> {days_left}\n\n"
            f"👥 <b>{t(lang, 'stats_invited')}:</b> {total_invited}\n"
            f"💎 <b>{t(lang, 'stats_bonuses')}:</b> {bonuses_received}"
        )
    else:
        msg = (
            f"{t(lang, 'stats_title')}\n\n"
            f"📅 <b>{t(lang, 'stats_plan')}:</b> {plan_label}\n"
            f"📍 <b>{t(lang, 'stats_expires')}:</b> {exp_str}\n"
            f"✨ <b>{t(lang, 'stats_days_left')}:</b> {days_left}\n\n"
            f"👥 <b>{t(lang, 'stats_invited')}:</b> {total_invited}\n"
            f"💎 <b>{t(lang, 'stats_bonuses')}:</b> {bonuses_received}"
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

        # Sync to 3X-UI panel
        if subscription.expires_at:
            from services.xui_service import ThreeXUIService
            xui = ThreeXUIService(
                xui_url=config.xui_url,
                username=config.xui_username,
                password=config.xui_password,
                inbound_id=config.xui_inbound_id,
            )
            try:
                email = f"id_{callback.from_user.id}"
                await xui.sync_client(client_uuid, email, sub_token, subscription.expires_at)
            except Exception as exc:
                import logging
                logging.getLogger(__name__).exception(
                    f"Failed to sync client {callback.from_user.id} to 3X-UI in get_config: {exc}"
                )

        # Перезагружаем подписку из БД
        subscription = db.get_subscription(callback.from_user.id)

    server_display_name = (
        config.primary_server.display_name
        .encode("utf-8", "surrogatepass")
        .decode("utf-8", "ignore")
    )
    sub_url = f"{config.subscription_config_base_url}/sub/{subscription.sub_token}"

    if lang == "ru":
        msg = (
            "💎 <b>Ваша премиум-подписка EDELIA | VPN</b>\n\n"
            "Используйте единую ссылку автообновления. Она автоматически продлевает доступ и поддерживает стабильное подключение без вашего участия.\n\n"
            "📍 <b>Ссылка для подключения:</b>\n"
            f"<code>{escape(sub_url)}</code>\n"
            "<i>(Нажмите на ссылку, чтобы скопировать её)</i>\n\n"
            "---\n"
            "📱 <b>Как настроить в 1 клик:</b>\n\n"
            "1. Скопируйте ссылку выше.\n"
            "2. Откройте ваше приложение (Hiddify, Shadowrocket, Nekobox или v2rayN).\n"
            "3. Нажмите <b>«Добавить подписку»</b> (или значок «+») и вставьте ссылку.\n\n"
            f"Подключение автоматически настроит локацию <b>{escape(server_display_name)}</b> в премиальном качестве."
        )
    else:
        msg = (
            "💎 <b>Your EDELIA | VPN Premium Subscription</b>\n\n"
            "Use the single auto-update link. It automatically renews your access and maintains a stable connection without your involvement.\n\n"
            "📍 <b>Connection Link:</b>\n"
            f"<code>{escape(sub_url)}</code>\n"
            "<i>(Tap the link to copy it)</i>\n\n"
            "---\n"
            "📱 <b>How to set up in 1 tap:</b>\n\n"
            "1. Copy the link above.\n"
            "2. Open your application (Hiddify, Shadowrocket, Nekobox, or v2rayN).\n"
            "3. Tap <b>\"Add subscription\"</b> (or the \"+\" icon) and paste the link.\n\n"
            f"The connection will automatically set up the <b>{escape(server_display_name)}</b> location in premium quality."
        )

    await edit_callback_message(
        callback,
        msg,
        reply_markup=_menu_keyboard(lang),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()
