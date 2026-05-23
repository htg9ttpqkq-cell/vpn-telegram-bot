"""Бизнес-логика подписок.

Ключевые изменения vs. предыдущей версии:
  1. activate_from_payment использует db.activate_subscription_with_referral()
     — единая ACID-транзакция (подписка + реферальный флаг).
  2. Реферальный бонус начисляется ТОЛЬКО за первую ПЛАТНУЮ активацию
     (plan != "trial"). Триал рефереру бонус не даёт.
  3. Добавлен expire_and_disable(user_id, bot) — для фонового cron:
     деактивирует в БД, дёргает XUI disable_client, уведомляет пользователя.
  4. Вызов 3X-UI (внешний API) остаётся ВНЕ транзакции — намеренно:
     деньги уплачены, подписка зафиксирована в БД. XUI-ошибка не откатывает
     финансовую часть, но логируется для ретрая оператором.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.handlers.ui_texts import plan_titles, texts
from core.config import PLANS, Config
from core.database import Database
from services.vpn_provision import generate_vless_link

logger = logging.getLogger(__name__)

# Дней бонуса рефереру за каждого оплатившего друга
REFERRAL_BONUS_DAYS = 30

# Планы, за которые реферер получает бонус (триал сюда НЕ входит)
_PAID_PLANS = frozenset(PLANS.keys()) - {"trial"}


def _ui_lang(stored: str) -> str:
    return "en" if stored == "en" else "ru"


class SubscriptionService:
    def __init__(self, db: Database, config: Config) -> None:
        self._db = db
        self._config = config
        from services.xui_service import ThreeXUIService

        # Инициализируем XUI-сервисы для всех настроенных серверов
        self._xui_services = {
            srv.code: ThreeXUIService(
                xui_url=srv.xui_url,
                username=srv.xui_username,
                password=srv.xui_password,
                inbound_id=srv.xui_inbound_id,
                display_name=srv.display_name,
            )
            for srv in config.servers
        }
        # Основной (первый) сервер — для всех текущих операций
        self._xui = self._xui_services.get(
            config.primary_server.code,
            list(self._xui_services.values())[0],
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_or_generate_tokens(
        self, current_sub
    ) -> tuple[str, str]:
        """Возвращает существующие sub_token/client_uuid или генерирует новые."""
        if current_sub and current_sub.sub_token and current_sub.client_uuid:
            return current_sub.sub_token, current_sub.client_uuid
        return secrets.token_urlsafe(16), str(uuid.uuid4())

    # ── Trial ─────────────────────────────────────────────────────────────────

    async def try_grant_welcome_trial(self, user_id: int) -> bool:
        """Одноразовые 7 дней для новых пользователей без активной подписки.

        Реферальный бонус за триал НЕ начисляется — только за платную активацию.
        """
        if not self._config.welcome_trial_enabled:
            return False
        if self._db.user_trial_consumed(user_id):
            return False
        trial_days = PLANS.get("trial")
        if trial_days is None:
            return False

        current = self._db.get_subscription(user_id)
        now = datetime.now(timezone.utc)
        if current and current.is_active and current.expires_at and current.expires_at > now:
            return False

        sub_token, client_uuid = self._get_or_generate_tokens(current)
        expires_at = now + timedelta(days=trial_days)
        vless_link = generate_vless_link(self._config.vless_template, client_uuid)

        # Атомарная транзакция: подписка + trial_consumed, без реферального бонуса
        self._db.activate_subscription_with_referral(
            user_id=user_id,
            plan="trial",
            expires_at=expires_at,
            vless_link=vless_link,
            sub_token=sub_token,
            client_uuid=client_uuid,
            referrer_id=None,   # триал НЕ активирует реферальный бонус
        )

        # Синхронизация с 3X-UI (вне транзакции — внешний API)
        try:
            email = f"id_{user_id}"
            await self._xui.sync_client(client_uuid, email, sub_token, expires_at)
        except Exception:
            logger.exception("Failed to sync trial client %d to 3X-UI", user_id)

        return True

    # ── Paid activation ───────────────────────────────────────────────────────

    async def activate_from_payment(self, user_id: int, plan: str) -> Dict[str, str]:
        """Активирует подписку после подтверждения оплаты.

        Алгоритм:
        1. Вычисляем новую дату окончания (продлеваем если была активна).
        2. Атомарно фиксируем в БД (подписка + реферальный флаг если план платный).
        3. Синхронизируем с 3X-UI (вне транзакции).
        4. Асинхронно начисляем бонусные дни рефереру (отдельно от активации).
        """
        days = PLANS.get(plan)
        if days is None:
            raise ValueError(f"Unknown plan: {plan!r}")

        self._db.upsert_user(user_id)
        current = self._db.get_subscription(user_id)
        now = datetime.now(timezone.utc)

        # Продлеваем от текущей даты окончания, если подписка ещё активна
        base_date = (
            current.expires_at
            if current and current.expires_at and current.expires_at > now
            else now
        )

        sub_token, client_uuid = self._get_or_generate_tokens(current)
        expires_at = base_date + timedelta(days=days)
        vless_link = generate_vless_link(self._config.vless_template, client_uuid)

        # Получаем ID реферера ТОЛЬКО для платных планов (не триал)
        referrer_id: Optional[int] = None
        if plan in _PAID_PLANS:
            referrer_id = self._db.get_referrer(user_id)

        # Единая ACID-транзакция: подписка + mark_referral_rewarded (если есть реферер)
        self._db.activate_subscription_with_referral(
            user_id=user_id,
            plan=plan,
            expires_at=expires_at,
            vless_link=vless_link,
            sub_token=sub_token,
            client_uuid=client_uuid,
            referrer_id=referrer_id,
        )

        # Синхронизация с 3X-UI (вне транзакции — внешний API)
        try:
            email = f"id_{user_id}"
            await self._xui.sync_client(client_uuid, email, sub_token, expires_at)
        except Exception:
            logger.exception("Failed to sync paid client %d to 3X-UI", user_id)

        # Начисляем бонусные дни рефереру (после успешной фиксации в БД)
        if referrer_id is not None:
            try:
                await self._add_bonus_days(referrer_id, REFERRAL_BONUS_DAYS)
                await self._notify_referrer_bonus(referrer_id)
            except Exception:
                logger.exception(
                    "Failed to process referral bonus for referrer=%d referred=%d",
                    referrer_id,
                    user_id,
                )

        return {
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M UTC"),
            "vless_link": vless_link,
            "plan": plan,
        }

    # ── Expiry (background cron) ──────────────────────────────────────────────

    async def expire_and_disable(self, sub, bot: Bot) -> None:
        """Деактивирует просроченную подписку и уведомляет пользователя.

        Вызывается фоновым планировщиком. Не бросает исключений наружу —
        логирует и продолжает обработку следующей записи.
        """
        user_id = sub.user_id
        try:
            # 1. Деактивируем в локальной БД
            self._db.deactivate_subscription(user_id)
            logger.info("Deactivated expired subscription for user %d", user_id)

            # 2. Деактивируем на панели 3X-UI (disable, не delete)
            if sub.client_uuid:
                email = f"id_{user_id}"
                try:
                    await self._xui.disable_client(sub.client_uuid, email)
                except Exception:
                    logger.exception(
                        "Failed to disable client %d (%s) on 3X-UI panel",
                        user_id, sub.client_uuid,
                    )

            # 3. Уведомляем пользователя в Telegram
            try:
                lang = _ui_lang(self._db.get_user_language(user_id))
                builder = InlineKeyboardBuilder()
                builder.button(
                    text=texts[lang]["btn_tariffs"], callback_data="buy_subscription"
                )
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"⚠️ <b>Ваша подписка EDELIA | VPN истекла.</b>\n\n"
                        f"Ваш доступ к VPN был автоматически приостановлен.\n"
                        f"Чтобы продолжить пользоваться защитой, продлите подписку:"
                        if lang == "ru"
                        else (
                            f"⚠️ <b>Your EDELIA | VPN subscription has expired.</b>\n\n"
                            f"Your VPN access has been automatically suspended.\n"
                            f"Renew your subscription to continue:"
                        )
                    ),
                    reply_markup=builder.as_markup(),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                logger.warning("Failed to notify user %d about expiry", user_id)

        except Exception:
            logger.exception(
                "Unexpected error in expire_and_disable for user %d", user_id
            )

    # ── Referral bonus ────────────────────────────────────────────────────────

    async def _add_bonus_days(self, user_id: int, days: int) -> None:
        """Добавляет бонусные дни к подписке реферера."""
        self._db.upsert_user(user_id)
        current = self._db.get_subscription(user_id)
        now = datetime.now(timezone.utc)

        sub_token, client_uuid = self._get_or_generate_tokens(current)

        base_date = (
            current.expires_at
            if current and current.is_active and current.expires_at and current.expires_at > now
            else now
        )
        expires_at = base_date + timedelta(days=days)
        vless_link = generate_vless_link(self._config.vless_template, client_uuid)
        plan = (current.plan if current and current.plan else "1m")

        # Обновляем подписку реферера (без реферального флага — это бонус)
        self._db.set_subscription(
            user_id,
            plan=plan,
            expires_at=expires_at,
            is_active=True,
            vless_link=vless_link,
            sub_token=sub_token,
            client_uuid=client_uuid,
        )

        try:
            email = f"id_{user_id}"
            await self._xui.sync_client(client_uuid, email, sub_token, expires_at)
        except Exception:
            logger.exception(
                "Failed to sync referral bonus for user %d to 3X-UI", user_id
            )

    async def _notify_referrer_bonus(self, referrer_id: int) -> None:
        """Уведомляет реферера о начислении бонуса."""
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
            logger.exception("Failed to notify referrer %d about bonus", referrer_id)
        finally:
            await bot.session.close()

    # ── User notifications ────────────────────────────────────────────────────

    async def notify_user_about_activation(
        self, user_id: int, payload: Dict[str, str]
    ) -> None:
        """Отправляет уведомление об успешной активации подписки."""
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
            logger.exception("Failed to notify user %d about activation", user_id)
        finally:
            await bot.session.close()
