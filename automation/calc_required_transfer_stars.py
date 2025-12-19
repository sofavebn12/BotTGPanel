from __future__ import annotations

import time
from typing import List

from telethon.tl.types import SavedStarGift


# Fixed cost per unique gift transfer (Telegram requirement)
TRANSFER_COST_PER_UNIQUE_GIFT = 15


def calc_required_transfer_stars(unique_gifts: List[SavedStarGift]) -> int:
    """
    Sums transfer cost (Stars) for unique gifts that are transferable now.
    Uses fixed cost of 15 Stars per unique gift transfer.
    If transfer is not available yet (can_transfer_at > now), ignores it.
    """
    now = int(time.time())
    count = 0
    for g in unique_gifts:
        can_transfer_at = getattr(g, "can_transfer_at", None)
        if isinstance(can_transfer_at, int) and can_transfer_at > now:
            continue
        # Count transferable unique gifts (each costs 15 Stars)
        count += 1
    return count * TRANSFER_COST_PER_UNIQUE_GIFT



