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
import re
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
        """Аутентификация в панели 3X-UI. Сессионная cookie и CSRF-токен сохраняются в client."""
        # 1. Сначала делаем GET запрос на корень, чтобы получить куки и CSRF-токен из мета-тегов
        url_get = f"{self.xui_url}/"
        try:
            resp_get = await client.get(url_get)
            resp_get.raise_for_status()
            
            # Извлекаем CSRF-токен
            match = re.search(r'<meta name="csrf-token" content="([^"]+)"', resp_get.text)
            if match:
                csrf_token = match.group(1)
                client.headers["x-csrf-token"] = csrf_token
                client.headers["referer"] = url_get
            else:
                logger.warning("CSRF token not found on 3X-UI landing page")
        except Exception as exc:
            logger.warning("Failed to fetch CSRF token from 3X-UI: %s", exc)

        # 2. Выполняем POST запрос на вход
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
        enable: bool = True,
    ) -> dict:
        """Формирует JSON-payload для отдельного клиента в 3X-UI v3.1.0."""
        return {
            "id": client_uuid,
            "email": email,
            "enable": enable,
            "flow": "",
            "limitIp": 0,
            "totalGB": 0,
            "expiryTime": expires_at_ms,
            "tgId": 0,
            "subId": sub_id,
            "reset": 0,
        }

    async def _get_client_by_email(
        self, client: httpx.AsyncClient, email: str
    ) -> Optional[dict]:
        """Возвращает данные клиента по email, если он существует в панели."""
        url = f"{self.xui_url}/panel/api/clients/get/{email}"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") and data.get("obj"):
                # Панель возвращает {"success":true,"msg":"","obj":{"client":{...},"inboundIds":[...]}}
                return data["obj"].get("client")
        except Exception as exc:
            logger.warning(
                "Could not check client existence for email %s: %s", email, exc
            )
        return None

    async def _try_add_client(
        self, client: httpx.AsyncClient, client_payload: dict, email: str, client_uuid: str
    ) -> bool:
        """Попытка добавить клиента. Возвращает True при успехе."""
        add_url = f"{self.xui_url}/panel/api/clients/add"
        payload = {
            "inboundIds": [self.inbound_id],
            "client": client_payload
        }
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
        self, client: httpx.AsyncClient, client_payload: dict, email: str, client_uuid: str
    ) -> None:
        """Обновляет существующего клиента. Raises ThreeXUIError при провале."""
        update_url = f"{self.xui_url}/panel/api/clients/update/{email}"
        payload = {
            **client_payload,
            "inboundIds": [self.inbound_id]
        }
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
        """Удаляет клиента по email."""
        url = f"{self.xui_url}/panel/api/clients/del/{email}"
        try:
            resp = await client.post(url)
            resp.raise_for_status()
            result = resp.json()
            if result.get("success"):
                logger.info(
                    "[%s] Deleted client by email %s",
                    self.display_name, email,
                )
            else:
                logger.warning(
                    "[%s] delClient by email (%s) returned: %s",
                    self.display_name, email, result.get("msg"),
                )
        except Exception as exc:
            logger.warning(
                "[%s] delClient by email (%s) exception: %s",
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
        """Создаёт или обновляет клиента в VLESS-инбаунде 3X-UI."""
        if not self.username or not self.password:
            logger.warning(
                "[%s] 3X-UI credentials not set — skipping sync.", self.display_name
            )
            return

        email = email.lower().strip()
        expires_at_ms = int(expires_at.timestamp() * 1000)
        client_payload = self._build_client_payload(
            client_uuid=client_uuid,
            email=email,
            sub_id=sub_id,
            expires_at_ms=expires_at_ms,
            enable=True,
        )

        async with httpx.AsyncClient(timeout=15.0) as http:
            await self._login(http)

            # Шаг 1: Проверяем, существует ли уже клиент с таким email
            existing_client = await self._get_client_by_email(http, email)

            if existing_client:
                # Шаг 2: Клиент существует
                # Проверяем, совпадает ли его UUID с требуемым client_uuid
                existing_uuid = existing_client.get("uuid") or existing_client.get("id")
                if existing_uuid == client_uuid:
                    # UUID совпадает -> просто обновляем настройки
                    logger.info(
                        "[%s] Client %s exists with matching UUID — attempting update.",
                        self.display_name, email,
                    )
                    await self._try_update_client(http, client_payload, email, client_uuid)
                else:
                    # UUID не совпадает -> удаляем старого клиента и создаем заново с новым UUID
                    logger.info(
                        "[%s] Client %s exists with different UUID (%s vs %s) — deleting and re-adding.",
                        self.display_name, email, existing_uuid, client_uuid,
                    )
                    await self._try_delete_by_email(http, email)
                    if not await self._try_add_client(http, client_payload, email, client_uuid):
                        raise ThreeXUIError(
                            f"[{self.display_name}] Failed to add client {email} after delete-on-UUID-mismatch."
                        )
            else:
                # Шаг 3: Клиент не существует -> создаем нового
                logger.info(
                    "[%s] Client %s does not exist — adding new client.",
                    self.display_name, email,
                )
                if not await self._try_add_client(http, client_payload, email, client_uuid):
                    # Попробуем очистить по email на всякий случай и повторить
                    logger.info(
                        "[%s] Failed to add client %s — cleaning up by email and retrying.",
                        self.display_name, email,
                    )
                    await self._try_delete_by_email(http, email)
                    if not await self._try_add_client(http, client_payload, email, client_uuid):
                        raise ThreeXUIError(
                            f"[{self.display_name}] Failed to sync client {email} ({client_uuid})."
                        )

    async def disable_client(self, client_uuid: str, email: str) -> None:
        """Деактивирует клиента на панели (enable=False), не удаляя запись."""
        if not self.username or not self.password:
            logger.warning(
                "[%s] 3X-UI credentials not set — skipping disable.", self.display_name
            )
            return

        email = email.lower().strip()
        async with httpx.AsyncClient(timeout=15.0) as http:
            try:
                await self._login(http)
            except ThreeXUIError as exc:
                logger.error(
                    "[%s] Cannot login to disable client %s: %s",
                    self.display_name, client_uuid, exc,
                )
                return

            existing_client = await self._get_client_by_email(http, email)
            if not existing_client:
                logger.info(
                    "[%s] disable_client: Client %s not found in panel — skipping.",
                    self.display_name, email,
                )
                return

            sub_id = existing_client.get("subId", "")
            client_payload = self._build_client_payload(
                client_uuid=client_uuid,
                email=email,
                sub_id=sub_id,
                expires_at_ms=1,  # 1 ms от эпохи = давно истёк
                enable=False,
            )
            await self._try_update_client(http, client_payload, email, client_uuid)

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
            await self._try_delete_by_email(http, email)
