import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add repository root to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_config
from services.xui_service import ThreeXUIService


async def test():
    config = load_config()
    print("XUI URL:", config.xui_url)
    print("XUI Username:", config.xui_username)
    print("XUI Inbound ID:", config.xui_inbound_id)

    if not config.xui_username or not config.xui_password:
        print("Error: XUI_USERNAME or XUI_PASSWORD are not configured in your .env file!")
        return

    xui = ThreeXUIService(
        xui_url=config.xui_url,
        username=config.xui_username,
        password=config.xui_password,
        inbound_id=config.xui_inbound_id,
    )

    test_uuid = "00000000-0000-0000-0000-999999999999"
    test_email = "id_99999999"
    test_sub = "test_sub_token_abc"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    print("\n--- Test 1: Syncing (Creating) Client ---")
    try:
        await xui.sync_client(test_uuid, test_email, test_sub, expires_at)
        print("SUCCESS: Client created/synced.")
    except Exception as exc:
        print(f"FAILED: {exc}")
        return

    print("\n--- Test 2: Syncing (Updating) Client ---")
    expires_at_new = expires_at + timedelta(days=30)
    try:
        await xui.sync_client(test_uuid, test_email, test_sub, expires_at_new)
        print("SUCCESS: Client updated.")
    except Exception as exc:
        print(f"FAILED: {exc}")
        return

    print("\n--- Test 3: Deleting Client ---")
    try:
        await xui.delete_client(test_uuid, test_email)
        print("SUCCESS: Client deleted.")
    except Exception as exc:
        print(f"FAILED: {exc}")
        return

    print("\nAll integration tests finished!")


if __name__ == "__main__":
    asyncio.run(test())
