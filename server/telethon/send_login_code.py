import asyncio

from telethon.errors import FloodWaitError

from server.store.in_memory_auth_state import AuthState, upsert_auth_state
from server.telethon.create_client import create_client


def send_login_code(*, user_id: str, phone_number: str) -> None:
    async def _run() -> None:
        client = create_client(user_id)
        await client.connect()
        try:
            sent = await client.send_code_request(phone_number)
            upsert_auth_state(
                AuthState(
                    user_id=user_id,
                    phone_number=phone_number,
                    phone_code_hash=sent.phone_code_hash,
                    is_authorized=False,
                )
            )
        finally:
            await client.disconnect()

    try:
        asyncio.run(_run())
    except FloodWaitError as e:
        raise RuntimeError(f"Flood wait: {e.seconds} seconds") from e








