"""Payment service layer.

Encapsulates the payment workflow: creating a pending record, confirming
or rejecting it, and updating related subscription state via
``SubscriptionService``.
"""

from typing import Dict, Optional

from core.config import Config
from core.database import Database
from services.subscription_service import SubscriptionService


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
        """Create a payment entry with status ``pending_review``."""
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
        """Mark payment as paid and activate the subscription."""
        payment = self._db.get_payment_by_id(payment_id)
        if payment is None:
            raise ValueError(f"Payment {payment_id} not found")
        if payment.status != "pending_review":
            raise ValueError("Payment already processed")

        activation = await self._subscription_service.activate_from_payment(
            payment.user_id, payment.plan
        )
        self._db.update_payment_status_by_id(payment_id, "paid")
        return activation

    def reject_payment(self, payment_id: int) -> None:
        """Mark payment as failed."""
        payment = self._db.get_payment_by_id(payment_id)
        if payment is None:
            raise ValueError(f"Payment {payment_id} not found")
        if payment.status != "pending_review":
            raise ValueError("Payment already processed")
        self._db.update_payment_status_by_id(payment_id, "failed")

    async def notify_user_about_activation(self, user_id: int, activation: Dict[str, str]) -> None:
        """Notify the user in Telegram after a successful activation."""
        await self._subscription_service.notify_user_about_activation(user_id, activation)
