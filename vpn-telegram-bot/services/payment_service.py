"""Payment service layer.

Ключевые изменения vs. предыдущей версии:
  - confirm_payment использует db.claim_payment_atomic() с BEGIN IMMEDIATE —
    защита от Double-Spending: параллельные нажатия "Confirm" вернут False.
  - reject_payment аналогично атомарно захватывает платёж.
"""

from typing import Dict, Optional

from core.config import Config
from core.database import Database
from services.subscription_service import SubscriptionService

import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """High-level API for manual SBP-style payments."""

    def __init__(self, db: Database, config: Config) -> None:
        self._db = db
        self._config = config
        self._subscription_service = SubscriptionService(db, config)

    def create_payment(
        self,
        user_id: int,
        plan: str,
        amount: int,
        comment: Optional[str] = None,
    ) -> int:
        """Создаёт запись платежа со статусом pending_review."""
        from uuid import uuid4

        return self._db.create_payment(
            user_id=user_id,
            plan=plan,
            amount=amount,
            status="pending_review",
            yookassa_payment_id=f"manual-{uuid4()}",
            idempotency_key=str(uuid4()),
            comment=comment,
        )

    async def confirm_payment(self, payment_id: int) -> Dict[str, str]:
        """Подтверждает платёж и активирует подписку.

        Защита от Double-Spending: claim_payment_atomic() использует
        BEGIN IMMEDIATE + UPDATE WHERE status='pending_review'.
        Второй параллельный вызов получит rowcount=0 и исключение.
        """
        # Атомарный захват: только первый вызов получает True
        claimed = self._db.claim_payment_atomic(payment_id)
        if not claimed:
            raise ValueError(
                f"Payment {payment_id} is already being processed or was already confirmed. "
                "Possible double-click — ignoring."
            )

        try:
            payment = self._db.get_payment_by_id(payment_id)
            if payment is None:
                raise ValueError(f"Payment {payment_id} not found after claim")

            activation = await self._subscription_service.activate_from_payment(
                payment.user_id, payment.plan
            )
            self._db.update_payment_status_by_id(payment_id, "paid")
            logger.info(
                "Payment #%d confirmed for user %d (plan=%s)",
                payment_id, payment.user_id, payment.plan,
            )
            return activation

        except Exception:
            # Откатываем статус обратно в pending_review чтобы можно было повторить
            self._db.update_payment_status_by_id(payment_id, "pending_review")
            logger.exception("Failed to confirm payment #%d — rolled back to pending_review", payment_id)
            raise

    def reject_payment(self, payment_id: int) -> None:
        """Отклоняет платёж атомарно — защита от двойного reject/confirm."""
        claimed = self._db.claim_payment_atomic(payment_id)
        if not claimed:
            raise ValueError(
                f"Payment {payment_id} is already being processed or confirmed."
            )
        self._db.update_payment_status_by_id(payment_id, "failed")
        logger.info("Payment #%d rejected", payment_id)

    async def notify_user_about_activation(
        self, user_id: int, activation: Dict[str, str]
    ) -> None:
        """Уведомляет пользователя об успешной активации."""
        await self._subscription_service.notify_user_about_activation(user_id, activation)
