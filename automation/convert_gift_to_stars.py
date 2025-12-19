from __future__ import annotations

from telethon import TelegramClient
from telethon.tl.functions.payments import ConvertStarGiftRequest
from telethon.tl.types import InputSavedStarGiftUser, SavedStarGift


async def convert_gift_to_stars(client: TelegramClient, saved_gift: SavedStarGift) -> bool:
    """
    Converts a saved gift to Stars (if convertible).
    Returns True if successful, False otherwise.
    """
    msg_id = getattr(saved_gift, "msg_id", None)
    if not isinstance(msg_id, int):
        return False

    convert_stars = getattr(saved_gift, "convert_stars", None)
    if not isinstance(convert_stars, int) or convert_stars <= 0:
        return False

    try:
        await client(
            ConvertStarGiftRequest(stargift=InputSavedStarGiftUser(msg_id=msg_id))
        )
        return True
    except Exception:
        return False






