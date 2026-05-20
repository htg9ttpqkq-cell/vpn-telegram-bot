import logging
from datetime import datetime, timedelta, timezone
from typing import Dict

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.handlers.ui_texts import plan_titles, texts
from core.config import PLANS, Config
import secrets
import uuid
from core.database import Database
from services.vpn_provision import generate_vless_link, vless_config_link

logger = logging.getLogger(__name__)

REFERRAL_BONUS_DAYS = 30  # +1 месяц за реферала


def _ui_lang(stored: str) -> str:
    return "en" if stored == "en" else "ru"


class SubscriptionService:
    def __init__(self, db: Database, config: Config) -> None:
        self._db = db
        self._config = config

    def try_grant_welcome_trial(self, user_id: int) -> bool:
        """Одноразовые 7 дней для новых пользователей без активной подписки."""
        if not self._config.welcome_trial_enabled:
            return False
        if self._db.user_trial_consumed(user_id):
            return False
        trial_days = PLANS.get("trial")
        if trial_days is None:
            return False
        current = self._db.get_subscription(user_id)
        now = datetime.now(timezone.utc)
        if (
            current
            and current.is_active
            and current.expires_at
            and current.expires_at > now
        ):
            return False

        if current and current.sub_token and current.client_uuid:
            sub_token = current.sub_token
            client_uuid = current.client_uuid
        else:
            sub_token = secrets.token_urlsafe(16)
            client_uuid = str(uuid.uuid4())

        expires_at = now + timedelta(days=trial_days)
        vless_link = generate_vless_link(self._config.vless_template, client_uuid)

        self._db.set_subscription(
            user_id,
            plan="trial",
            expires_at=expires_at,
            is_active=True,
            vless_link=vless_link,
            sub_token=sub_token,
            client_uuid=client_uuid,
        )
        self._db.set_trial_consumed(user_id)
        return True

    async def activate_from_payment(self, user_id: int, plan: str) -> Dict[str, str]:
        days = PLANS.get(plan)
        if days is None:
            raise ValueError("Unknown plan")

        self._db.upsert_user(user_id)
        current = self._db.get_subscription(user_id)
        now = datetime.now(timezone.utc)
        base_date = now
        if current and current.expires_at and current.expires_at > now:
            base_date = current.expires_at

        if current and current.sub_token and current.client_uuid:
            sub_token = current.sub_token
            client_uuid = current.client_uuid
        else:
            sub_token = secrets.token_urlsafe(16)
            client_uuid = str(uuid.uuid4())

        expires_at = base_date + timedelta(days=days)
        vless_link = generate_vless_link(self._config.vless_template, client_uuid)

        self._db.set_subscription(
            user_id,
            plan=plan,
            expires_at=expires_at,
            is_active=True,
            vless_link=vless_link,
            sub_token=sub_token,
            client_uuid=client_uuid,
        )
        self._db.set_trial_consumed(user_id)
        # Проверяем наличие реферера и начисляем ему бонус
        await self._process_referral_reward(user_id)
        return {
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M UTC"),
            "vless_link": vless_link,
            "plan": plan,
        }

    async def _process_referral_reward(self, referred_id: int) -> None:
        """If user was referred, grant referrer +30 days and send notification."""
        referrer_id = self._db.get_referrer(referred_id)
        if referrer_id is None:
            return
        try:
            self._add_bonus_days(referrer_id, REFERRAL_BONUS_DAYS)
            self._db.mark_referral_rewarded(referrer_id, referred_id)
            await self._notify_referrer_bonus(referrer_id)
        except Exception:
            logger.exception(
                "Failed to process referral reward for referrer=%s referred=%s",
                referrer_id,
                referred_id,
            )

    def _add_bonus_days(self, user_id: int, days: int) -> None:
        """Adds bonus days to user's subscription."""
        self._db.upsert_user(user_id)
        current = self._db.get_subscription(user_id)
        now = datetime.now(timezone.utc)

        if current and current.sub_token and current.client_uuid:
            sub_token = current.sub_token
            client_uuid = current.client_uuid
        else:
            sub_token = secrets.token_urlsafe(16)
            client_uuid = str(uuid.uuid4())

        # Если подписка активна — продлеваем от текущей даты окончания
        if current and current.is_active and current.expires_at and current.expires_at > now:
            base_date = current.expires_at
        else:
            base_date = now

        expires_at = base_date + timedelta(days=days)
        vless_link = generate_vless_link(self._config.vless_template, client_uuid)
        plan = (current.plan if current and current.plan else "1m")

        self._db.set_subscription(
            user_id,
            plan=plan,
            expires_at=expires_at,
            is_active=True,
            vless_link=vless_link,
            sub_token=sub_token,
            client_uuid=client_uuid,
        )

    async def _notify_referrer_bonus(self, referrer_id: int) -> None:
        """Sends a notification to the referrer about receiving a bonus month."""
        bot = Bot(token=self._config.bot_token)
        try:
            lk = _ui_lang(self._db.get_user_language(referrer_id))
            builder = InlineKeyboardBuilder()
            builder.button(text=texts[lk]["btn_profile"], callback_data="my_subscription")
            await bot.send_message(
                chat_id=referrer_id,
                text=texts[lk]["invite_bonus_received"],
                reply_markup=builder.as_markup(),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            logger.exception("Failed to notify referrer %s about bonus", referrer_id)
        finally:
            await bot.session.close()

    async def notify_user_about_activation(self, user_id: int, payload: Dict[str, str]) -> None:
        bot = Bot(token=self._config.bot_token)
        try:
            lk = _ui_lang(self._db.get_user_language(user_id))
            plan_label = plan_titles[lk].get(payload["plan"], payload["plan"])
            builder = InlineKeyboardBuilder()
            builder.button(text=texts[lk]["btn_get_config"], callback_data="get_config")
            builder.button(text=texts[lk]["btn_setup_guide"], callback_data="setup_guide")
            builder.adjust(1)
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"{texts[lk]['activation_intro']}\n\n"
                    f"{texts[lk]['profile_plan']}: {plan_label}\n"
                    f"{texts[lk]['profile_expiry']}: {payload['expires_at']}"
                ),
                reply_markup=builder.as_markup(),
            )
        except Exception:
            logger.exception("Failed to notify user %s about activation", user_id)
        finally:
            await bot.session.close()
