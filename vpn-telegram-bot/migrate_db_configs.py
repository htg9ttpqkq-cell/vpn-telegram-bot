import asyncio
import sys
import os
import secrets
import uuid
from datetime import datetime, timezone

# Add repository root/vpn-telegram-bot to python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vpn-telegram-bot"))

from core.config import load_config
from core.database import Database
from services.vpn_provision import generate_vless_link
from services.xui_service import ThreeXUIService

async def main():
    config = load_config()
    db = Database(config.db_path)
    db.init()

    xui = ThreeXUIService(
        xui_url=config.xui_url,
        username=config.xui_username,
        password=config.xui_password,
        inbound_id=config.xui_inbound_id,
    )

    print("Loading all active subscriptions from database...")
    with db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, plan, expires_at, is_active, vless_link, sub_token, client_uuid 
            FROM subscriptions 
            WHERE is_active = 1
        """)
        rows = cursor.fetchall()
        
    print(f"Found {len(rows)} active subscriptions.")

    updated_count = 0
    synced_count = 0

    for row in rows:
        user_id, plan, expires_at_str, is_active, old_vless_link, old_sub_token, old_client_uuid = row
        print(f"\nProcessing user {user_id}:")
        
        # 1. Ensure UUID and sub_token are present
        client_uuid = old_client_uuid or str(uuid.uuid4())
        sub_token = old_sub_token or secrets.token_urlsafe(16)
        
        # Parse expires_at
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except Exception:
            expires_at = datetime.now(timezone.utc)

        # 2. Generate updated VLESS link
        vless_link = generate_vless_link(config.vless_template, client_uuid)
        
        needs_db_update = (
            old_client_uuid != client_uuid or 
            old_sub_token != sub_token or 
            (old_vless_link or "").strip() != vless_link.strip()
        )

        if needs_db_update:
            print(f"  -> Updating database settings (port 1500, new keys/UUID/token)")
            db.set_subscription(
                user_id=user_id,
                plan=plan or "trial",
                expires_at=expires_at,
                is_active=True,
                vless_link=vless_link,
                sub_token=sub_token,
                client_uuid=client_uuid,
            )
            updated_count += 1
        else:
            print("  -> Database config is already up to date")

        # 3. Sync to 3X-UI panel
        try:
            email = f"id_{user_id}"
            await xui.sync_client(client_uuid, email, sub_token, expires_at)
            print("  -> Successfully synced to 3X-UI panel")
            synced_count += 1
        except Exception as exc:
            print(f"  -> ERROR syncing to 3X-UI panel: {exc}")

    print(f"\nMigration finished!")
    print(f"Updated in database: {updated_count} rows")
    print(f"Synced to 3X-UI panel: {synced_count} clients")

if __name__ == "__main__":
    asyncio.run(main())
