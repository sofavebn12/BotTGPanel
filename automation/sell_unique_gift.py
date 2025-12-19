from __future__ import annotations

from telethon import TelegramClient
from telethon.tl.functions.payments import UpdateStarGiftPriceRequest
from telethon.tl.types import InputSavedStarGiftUser, SavedStarGift


async def sell_unique_gift(
    client: TelegramClient, saved_gift: SavedStarGift, price_stars: int
) -> bool:
    """
    Lists a unique gift for resale at the specified price (in Stars).
    Returns True if successful, False otherwise.
    """
    msg_id = getattr(saved_gift, "msg_id", None)
    if not isinstance(msg_id, int):
        return False

    try:
        from telethon.tl.types import StarsAmount

        # Create StarsAmount for price
        stars_amount = StarsAmount(amount=price_stars, nanos=0)

        # List gift for resale
        await client(
            UpdateStarGiftPriceRequest(
                stargift=InputSavedStarGiftUser(msg_id=msg_id),
                resell_amount=stars_amount,
            )
        )
        return True
    except Exception:
        return False






