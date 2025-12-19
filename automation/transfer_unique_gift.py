from __future__ import annotations

from telethon import TelegramClient
from telethon.tl.functions.payments import TransferStarGiftRequest
from telethon.tl.types import InputPeerUser, InputSavedStarGiftUser, SavedStarGift


async def transfer_unique_gift(
    client: TelegramClient, saved_gift: SavedStarGift, recipient_user_id: int
) -> bool:
    """
    Transfers a unique gift to another user.
    Returns True if successful, False otherwise.
    """
    msg_id = getattr(saved_gift, "msg_id", None)
    if not isinstance(msg_id, int):
        return False

    try:
        # Get recipient peer
        recipient_peer = await client.get_input_entity(recipient_user_id)
        if not isinstance(recipient_peer, InputPeerUser):
            return False

        # Transfer gift
        await client(
            TransferStarGiftRequest(
                stargift=InputSavedStarGiftUser(msg_id=msg_id),
                to_id=recipient_peer,
            )
        )
        return True
    except Exception:
        return False






