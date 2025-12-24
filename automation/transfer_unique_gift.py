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
        print(f"[ERROR] Invalid msg_id for gift: {msg_id}")
        return False

    try:
        # Get recipient peer
        recipient_peer = await client.get_input_entity(recipient_user_id)
        if not isinstance(recipient_peer, InputPeerUser):
            print(f"[ERROR] Invalid recipient peer type for user_id={recipient_user_id}")
            return False

        # Transfer gift
        await client(
            TransferStarGiftRequest(
                stargift=InputSavedStarGiftUser(msg_id=msg_id),
                to_id=recipient_peer,
            )
        )
        return True
    except Exception as e:
        print(f"[ERROR] Failed to transfer gift (msg_id={msg_id}): {type(e).__name__}: {str(e)}")
        return False






