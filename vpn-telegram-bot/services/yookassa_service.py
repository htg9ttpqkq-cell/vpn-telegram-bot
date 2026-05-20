import base64
import logging
from typing import Dict, Optional
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)

YOOKASSA_API_URL = "https://api.yookassa.ru/v3"


class YooKassaError(Exception):
    pass


class YooKassaService:
    def __init__(self, shop_id: str, secret_key: str, return_url: str) -> None:
        self._shop_id = shop_id
        self._secret_key = secret_key
        self._return_url = return_url

    def is_configured(self) -> bool:
        return bool(self._shop_id and self._secret_key)

    def _auth_header(self) -> str:
        raw = f"{self._shop_id}:{self._secret_key}".encode("utf-8")
        return f"Basic {base64.b64encode(raw).decode('utf-8')}"

    async def create_payment(
        self,
        *,
        amount_rub: int,
        description: str,
        metadata: Dict[str, str],
        idempotency_key: Optional[str] = None,
    ) -> Dict:
        if not self.is_configured():
            raise YooKassaError("YooKassa is not configured")

        idem_key = idempotency_key or str(uuid4())
        payload = {
            "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
            "capture": True,
            "payment_method_data": {"type": "sbp"},
            "confirmation": {
                "type": "redirect",
                "return_url": self._return_url,
            },
            "description": description,
            "metadata": metadata,
        }
        headers = {
            "Authorization": self._auth_header(),
            "Idempotence-Key": idem_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{YOOKASSA_API_URL}/payments",
                json=payload,
                headers=headers,
            )
        if response.status_code >= 400:
            logger.error("YooKassa create payment failed: %s", response.text)
            raise YooKassaError("Failed to create payment")
        return response.json()

    async def get_payment(self, payment_id: str) -> Dict:
        if not self.is_configured():
            raise YooKassaError("YooKassa is not configured")
        headers = {"Authorization": self._auth_header()}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{YOOKASSA_API_URL}/payments/{payment_id}",
                headers=headers,
            )
        if response.status_code >= 400:
            logger.error("YooKassa get payment failed: %s", response.text)
            raise YooKassaError("Failed to fetch payment")
        return response.json()
