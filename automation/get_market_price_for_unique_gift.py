from __future__ import annotations

from typing import Optional

from telethon import TelegramClient
from telethon.tl.functions.payments import GetResaleStarGiftsRequest
from telethon.tl.types import SavedStarGift, StarGiftUnique


async def get_market_price_for_unique_gift(
    client: TelegramClient, saved_gift: SavedStarGift
) -> Optional[int]:
    """
    Gets the minimum market price (in Stars) for a unique gift by checking resale listings.
    Returns None if no listings found or gift is not unique.
    """
    gift = getattr(saved_gift, "gift", None)
    if not isinstance(gift, StarGiftUnique):
        return None

    gift_id = getattr(gift, "gift_id", None)
    if not isinstance(gift_id, int):
        return None

    try:
        # Fetch resale listings for this gift type, sorted by price (ascending)
        res = await client(GetResaleStarGiftsRequest(
            gift_id=gift_id,
            sort_by_price=True,  # Sort by price ascending
            offset="",
            limit=10,  # Check first 10 listings
        ))

        if not hasattr(res, "gifts") or not res.gifts:
            return None

        # Find minimum price from listings
        min_price = None
        for listing_gift in res.gifts:
            resell_amount = getattr(listing_gift, "resell_amount", None)
            if resell_amount:
                # resell_amount is Vector<StarsAmount>, take first if exists
                if isinstance(resell_amount, list) and len(resell_amount) > 0:
                    stars_amt = resell_amount[0]
                    amount = getattr(stars_amt, "amount", None)
                    if isinstance(amount, int):
                        if min_price is None or amount < min_price:
                            min_price = amount

        return min_price
    except Exception:
        return None






