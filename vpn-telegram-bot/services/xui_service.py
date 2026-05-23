"""Клиент для API панели 3X-UI.

Логика sync_client (исправление ошибки "empty client ID"):
  1. Пробуем addClient → если успех, выходим.
  2. Если add провалился → проверяем существование клиента по UUID
     через GET /panel/api/inbounds/getClientTrafficsById/{uuid}.
  3. Если клиент существует → updateClient (он точно в этом inbound).
  4. Если клиент НЕ существует → пробуем удалить по email (мог быть
     создан с другим UUID) и повторяем addClient.
"""

import json
import logging
import httpx
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ThreeXUIError(Exception):
    pass


class ThreeXUIService:
    def __init__(
        self,
        xui_url: str,
        username: str,
        password: str,
        inbound_id: int = 1,
        display_name: str = "3X-UI",
    ) -> None:
        self.xui_url = xui_url.rstrip("/")
        self.username = username
        self.password = password
        self.inbound_id = inbound_id
        self.display_name = display_name  # для удобочитаемых логов

    # ── Authentication ────────────────────────────────────────────────────────

    async def _login(self, client: httpx.AsyncClient) -> None:
        """Аутентификация в панели 3X-UI. Сессионная cookie сохраняется в client."""
        login_url = f"{self.xui_url}/login"
        try:
            resp = await client.post(
                login_url,
                json={"username": self.username, "password": self.password},
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                raise ThreeXUIError(
                    f"Login failed: {data.get('msg', 'unknown error')}"
                )
        except ThreeXUIError:
            raise
        except Exception as exc:
            raise ThreeXUIError(
                f"Failed to authenticate with 3X-UI at {login_url}: {exc}"
            ) from exc

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _build_client_payload(
        self,
        client_uuid: str,
        email: str,
        sub_id: str,
        expires_at_ms: int,
    ) -> dict:
        """Формирует JSON-payload для addClient / updateClient.

        Структура, ожидаемая 3X-UI:
        {
            "id": <inbound_id: int>,        ← ID инбаунда как целое число
            "settings": "<JSON-строка>"     ← settings сериализуется в строку
        }
        Внутри settings.clients[0].id — UUID клиента.
        """
        clients_data = {
            "clients": [
                {
                    "id": client_uuid,      # UUID клиента в строковом виде
                    "email": email,
                    "enable": True,
                    "flow": "",
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": expires_at_ms,
                    "tgId": "",
                    "subId": sub_id,
                    "reset": 0,
                }
            ]
        }
        return {
            "id": self.inbound_id,          # int, не строка
            "settings": json.dumps(clients_data),
        }

    async def _client_exists(
        self, client: httpx.AsyncClient, client_uuid: str
    ) -> bool:
        """Проверяет, зарегистрирован ли UUID в панели (любой inbound)."""
        url = f"{self.xui_url}/panel/api/inbounds/getClientTrafficsById/{client_uuid}"
        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                return False
            resp.raise_for_status()
            data = resp.json()
            # Панель возвращает {"success": true, "obj": {...}} если клиент есть
            return bool(data.get("success") and data.get("obj"))
        except Exception as exc:
            logger.warning(
                "Could not check client existence for UUID %s: %s", client_uuid, exc
            )
            # Не можем проверить → предполагаем, что клиента нет
            return False

    async def _try_add_client(
        self, client: httpx.AsyncClient, payload: dict, email: str, client_uuid: str
    ) -> bool:
        """Попытка добавить клиента. Возвращает True при успехе."""
        add_url = f"{self.xui_url}/panel/api/inbounds/addClient"
        try:
            resp = await client.post(add_url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            if result.get("success"):
                logger.info(
                    "[%s] Added client %s (%s) to inbound %d",
                    self.display_name, email, client_uuid, self.inbound_id,
                )
                return True
            logger.info(
                "[%s] addClient returned failure for %s (%s): %s",
                self.display_name, email, client_uuid, result.get("msg", ""),
            )
        except Exception as exc:
            logger.warning(
                "[%s] addClient exception for %s (%s): %s",
                self.display_name, email, client_uuid, exc,
            )
        return False

    async def _try_update_client(
        self, client: httpx.AsyncClient, payload: dict, email: str, client_uuid: str
    ) -> None:
        """Обновляет существующего клиента. Raises ThreeXUIError при провале."""
        update_url = (
            f"{self.xui_url}/panel/api/inbounds/updateClient/{client_uuid}"
        )
        try:
            resp = await client.post(update_url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            if not result.get("success"):
                raise ThreeXUIError(
                    f"updateClient failed: {result.get('msg', 'unknown error')}"
                )
            logger.info(
                "[%s] Updated client %s (%s) in inbound %d",
                self.display_name, email, client_uuid, self.inbound_id,
            )
        except ThreeXUIError:
            raise
        except Exception as exc:
            raise ThreeXUIError(
                f"updateClient exception for {email} ({client_uuid}): {exc}"
            ) from exc

    async def _try_delete_by_email(
        self, client: httpx.AsyncClient, email: str
    ) -> None:
        """Удаляет клиента по email (fallback при коллизии UUID)."""
        url = f"{self.xui_url}/panel/api/inbounds/{self.inbound_id}/delClientByEmail/{email}"
        try:
            resp = await client.post(url)
            resp.raise_for_status()
            result = resp.json()
            if result.get("success"):
                logger.info(
                    "[%s] Deleted stale client by email %s from inbound %d",
                    self.display_name, email, self.inbound_id,
                )
            else:
                logger.warning(
                    "[%s] delClientByEmail(%s) returned: %s",
                    self.display_name, email, result.get("msg"),
                )
        except Exception as exc:
            logger.warning(
                "[%s] delClientByEmail(%s) exception: %s",
                self.display_name, email, exc,
            )

    # ── Public API ────────────────────────────────────────────────────────────

    async def sync_client(
        self,
        client_uuid: str,
        email: str,
        sub_id: str,
        expires_at: datetime,
    ) -> None:
        """Создаёт или обновляет клиента в VLESS-инбаунде 3X-UI.

        Алгоритм (защита от «empty client ID»):
        1. addClient → успех → выход.
        2. add провалился → проверяем существование UUID через
           getClientTrafficsById.
        3. UUID существует → updateClient.
        4. UUID не существует → удаляем по email (могла быть старая запись)
           и повторяем addClient.
        """
        if not self.username or not self.password:
            logger.warning(
                "[%s] 3X-UI credentials not set — skipping sync.", self.display_name
            )
            return

        email = email.lower().strip()
        # Панель принимает миллисекунды с эпохи
        expires_at_ms = int(expires_at.timestamp() * 1000)
        payload = self._build_client_payload(client_uuid, email, sub_id, expires_at_ms)

        async with httpx.AsyncClient(timeout=15.0) as http:
            await self._login(http)

            # Шаг 1: попытка добавить клиента
            if await self._try_add_client(http, payload, email, client_uuid):
                return

            # Шаг 2: проверяем, существует ли UUID в панели
            exists = await self._client_exists(http, client_uuid)

            if exists:
                # Шаг 3а: UUID зарегистрирован → просто обновляем
                logger.info(
                    "[%s] Client %s exists — attempting updateClient.",
                    self.display_name, client_uuid,
                )
                await self._try_update_client(http, payload, email, client_uuid)
            else:
                # Шаг 3б: UUID не найден → удаляем старую запись по email (если есть)
                # и снова добавляем (чистый add должен сработать)
                logger.info(
                    "[%s] Client %s not found by UUID — cleaning up email %s and re-adding.",
                    self.display_name, client_uuid, email,
                )
                await self._try_delete_by_email(http, email)
                if not await self._try_add_client(http, payload, email, client_uuid):
                    raise ThreeXUIError(
                        f"[{self.display_name}] Failed to sync client {email} "
                        f"({client_uuid}) after delete-and-retry."
                    )

    async def delete_client(self, client_uuid: str, email: str) -> None:
        """Удаляет клиента из VLESS-инбаунда 3X-UI."""
        if not self.username or not self.password:
            logger.warning(
                "[%s] 3X-UI credentials not set — skipping delete.", self.display_name
            )
            return

        email = email.lower().strip()
        async with httpx.AsyncClient(timeout=15.0) as http:
            await self._login(http)
            del_url = (
                f"{self.xui_url}/panel/api/inbounds/{self.inbound_id}"
                f"/delClient/{client_uuid}"
            )
            try:
                resp = await http.post(del_url)
                resp.raise_for_status()
                result = resp.json()
                if not result.get("success"):
                    logger.warning(
                        "[%s] delClient by UUID %s failed: %s. Trying by email...",
                        self.display_name, client_uuid, result.get("msg"),
                    )
                    await self._try_delete_by_email(http, email)
                else:
                    logger.info(
                        "[%s] Deleted client %s (%s) from inbound %d",
                        self.display_name, email, client_uuid, self.inbound_id,
                    )
            except Exception as exc:
                logger.warning(
                    "[%s] Failed to delete client %s (%s) from 3X-UI: %s",
                    self.display_name, email, client_uuid, exc,
                )
