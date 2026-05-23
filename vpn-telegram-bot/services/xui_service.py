import json
import logging
import httpx
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ThreeXUIError(Exception):
    pass


class ThreeXUIService:
    def __init__(self, xui_url: str, username: str, password: str, inbound_id: int = 1) -> None:
        self.xui_url = xui_url.rstrip("/")
        self.username = username
        self.password = password
        self.inbound_id = inbound_id

    async def _login(self, client: httpx.AsyncClient) -> None:
        login_url = f"{self.xui_url}/login"
        try:
            resp = await client.post(
                login_url,
                json={"username": self.username, "password": self.password}
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                raise ThreeXUIError(f"Login failed: {data.get('msg', 'unknown error')}")
        except Exception as exc:
            raise ThreeXUIError(f"Failed to authenticate with 3X-UI at {login_url}: {exc}") from exc

    async def sync_client(self, client_uuid: str, email: str, sub_id: str, expires_at: datetime) -> None:
        """Adds or updates a client in the VLESS inbound on 3X-UI."""
        if not self.username or not self.password:
            logger.warning("3X-UI credentials not set. Skipping sync.")
            return

        email = email.lower().strip()
        # Convert expires_at to timestamp in milliseconds
        expires_at_ms = int(expires_at.timestamp() * 1000)

        # 3X-UI addClient/updateClient expects settings to be a JSON stringified object
        clients_data = {
            "clients": [{
                "id": client_uuid,
                "email": email,
                "enable": True,
                "flow": "",
                "limitIp": 0,
                "totalGB": 0,
                "expiryTime": expires_at_ms,
                "tgId": "",
                "subId": sub_id,
                "reset": 0
            }]
        }

        payload = {
            "id": self.inbound_id,
            "settings": json.dumps(clients_data)
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            await self._login(client)
            add_url = f"{self.xui_url}/panel/api/inbounds/addClient"
            try:
                resp = await client.post(add_url, json=payload)
                resp.raise_for_status()
                result = resp.json()
                if result.get("success"):
                    logger.info(f"Successfully added client {email} ({client_uuid}) to 3X-UI inbound {self.inbound_id}.")
                    return

                msg = result.get("msg", "")
                logger.info(f"Failed to add client {email} ({client_uuid}): {msg}. Attempting to update instead.")
            except Exception as exc:
                logger.info(f"Exception while adding client {email}: {exc}. Attempting update.")

            # Update client
            update_url = f"{self.xui_url}/panel/api/inbounds/updateClient/{client_uuid}"
            try:
                resp = await client.post(update_url, json=payload)
                resp.raise_for_status()
                result = resp.json()
                if not result.get("success"):
                    raise ThreeXUIError(f"Failed to update client: {result.get('msg', 'unknown error')}")
                logger.info(f"Successfully updated client {email} ({client_uuid}) in 3X-UI inbound {self.inbound_id}.")
            except Exception as exc:
                raise ThreeXUIError(f"Failed to sync client {email} to 3X-UI: {exc}") from exc

    async def delete_client(self, client_uuid: str, email: str) -> None:
        """Deletes a client from the VLESS inbound on 3X-UI."""
        if not self.username or not self.password:
            logger.warning("3X-UI credentials not set. Skipping delete.")
            return

        email = email.lower().strip()
        async with httpx.AsyncClient(timeout=10.0) as client:
            await self._login(client)
            del_url = f"{self.xui_url}/panel/api/inbounds/{self.inbound_id}/delClient/{client_uuid}"
            try:
                resp = await client.post(del_url)
                resp.raise_for_status()
                result = resp.json()
                if not result.get("success"):
                    logger.warning(f"Failed to delete client {client_uuid} by UUID: {result.get('msg')}. Trying by email...")
                    del_email_url = f"{self.xui_url}/panel/api/inbounds/{self.inbound_id}/delClientByEmail/{email}"
                    resp_email = await client.post(del_email_url)
                    resp_email.raise_for_status()
                    result_email = resp_email.json()
                    if not result_email.get("success"):
                        raise ThreeXUIError(f"Failed to delete client by email: {result_email.get('msg')}")
                logger.info(f"Successfully deleted client {email} ({client_uuid}) from 3X-UI inbound {self.inbound_id}.")
            except Exception as exc:
                logger.warning(f"Failed to delete client {email} ({client_uuid}) from 3X-UI: {exc}")
