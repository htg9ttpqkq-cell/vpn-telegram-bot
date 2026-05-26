import logging
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)

PLATEGA_API_URL = "https://app.platega.io"


class PlategaError(Exception):
    pass


class PlategaService:
    def __init__(self, merchant_id: str, secret_key: str, return_url: str) -> None:
        self._merchant_id = merchant_id
        self._secret_key = secret_key
        self._return_url = return_url

    def is_configured(self) -> bool:
        return bool(self._merchant_id and self._secret_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "X-MerchantId": self._merchant_id,
            "X-Secret": self._secret_key,
            "Content-Type": "application/json",
        }

    async def create_payment(
        self,
        *,
        amount_rub: float,
        description: str,
        payload: str,
    ) -> Dict:
        """Создает транзакцию оплаты в Platega.io (API v2).

        Реальный ответ API:
          {
            "transactionId": "...",
            "status": "PENDING",
            "url": "https://pay.platega.io?id=...",
            "expiresIn": "00:30:00",
            "rate": 0
          }
        """
        if not self.is_configured():
            raise PlategaError("Platega is not configured")

        request_payload = {
            "paymentDetails": {
                "amount": amount_rub,
                "currency": "RUB",
            },
            "description": description,
            "return": self._return_url,
            "failedUrl": self._return_url,
            "payload": payload,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{PLATEGA_API_URL}/v2/transaction/process",
                json=request_payload,
                headers=self._headers(),
            )

        if response.status_code >= 400:
            logger.error("Platega create payment failed: %d %s", response.status_code, response.text)
            raise PlategaError(f"Failed to create Platega payment: {response.text}")

        data = response.json()
        logger.debug("Platega create_payment response: %s", data)
        return data

    async def get_payment(self, transaction_id: str) -> Dict:
        """Получает детальную информацию о транзакции, включая статус."""
        if not self.is_configured():
            raise PlategaError("Platega is not configured")

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{PLATEGA_API_URL}/transaction/{transaction_id}",
                headers=self._headers(),
            )

        if response.status_code >= 400:
            logger.error("Platega get payment failed: %d %s", response.status_code, response.text)
            raise PlategaError(f"Failed to fetch Platega payment status: {response.text}")

        return response.json()
