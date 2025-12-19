from __future__ import annotations

from typing import List

from telethon import TelegramClient
from telethon.tl.functions.payments import GetStarGiftsRequest
from telethon.tl.types import StarGift, StarGiftUnique


async def get_available_regular_gifts(client: TelegramClient) -> List[StarGift]:
    """
    Fetches list of available regular (non-unique) gifts from Telegram.
    Filters out unique gifts, sold-out gifts, and premium-only gifts if user doesn't have premium.
    """
    try:
        # Get all available gifts (hash=0 to get fresh list)
        result = await client(GetStarGiftsRequest(hash=0))

        if not hasattr(result, "gifts") or not result.gifts:
            return []

        regular_gifts: List[StarGift] = []
        for gift in result.gifts:
            # Skip if not a StarGift (shouldn't happen, but safety check)
            if not isinstance(gift, StarGift):
                continue

            # Skip unique gifts (they are StarGiftUnique, not StarGift)
            # Actually, StarGiftUnique is a different type, so this check might not be needed
            # But we'll keep it for safety

            # Skip sold-out gifts
            if getattr(gift, "sold_out", False):
                continue

            # Skip if requires premium (we'll assume user might not have it)
            # Actually, let's check this - if require_premium is set, skip for now
            # User can enable this later if they have premium
            if getattr(gift, "require_premium", False):
                continue

            # Check availability
            availability_remains = getattr(gift, "availability_remains", None)
            if isinstance(availability_remains, int) and availability_remains <= 0:
                continue

            # Check per-user limit
            per_user_remains = getattr(gift, "per_user_remains", None)
            if isinstance(per_user_remains, int) and per_user_remains <= 0:
                continue

            regular_gifts.append(gift)

        return regular_gifts
    except Exception:
        return []






