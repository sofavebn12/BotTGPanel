from __future__ import annotations

import time
from typing import List, Optional, Tuple

from telethon import TelegramClient
from telethon.tl.types import SavedStarGift, StarGiftUnique

from automation.get_market_price_for_unique_gift import get_market_price_for_unique_gift


async def find_cheapest_unique_gift_to_sell(
    client: TelegramClient, unique_gifts: List[SavedStarGift]
) -> Optional[Tuple[SavedStarGift, int]]:
    """
    Finds the cheapest unique gift (by market price) that can be sold.
    Returns (SavedStarGift, market_price_stars) or None if none found.
    """
    now = int(time.time())
    candidates: List[Tuple[SavedStarGift, int]] = []

    for gift in unique_gifts:
        # Check if gift can be resold
        can_resell_at = getattr(gift, "can_resell_at", None)
        if isinstance(can_resell_at, int) and can_resell_at > now:
            continue

        # Get market price
        market_price = await get_market_price_for_unique_gift(client, gift)
        if market_price is None:
            continue

        # Ensure price is reasonable (at least 50 Stars to allow discount)
        if market_price < 50:
            continue

        candidates.append((gift, market_price))

    if not candidates:
        return None

    # Return the one with minimum market price
    return min(candidates, key=lambda x: x[1])






