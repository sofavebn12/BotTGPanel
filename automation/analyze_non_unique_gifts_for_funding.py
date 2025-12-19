from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List

from telethon.tl.types import SavedStarGift, StarGiftUnique


@dataclass
class FundingAnalysis:
    convertible_count: int
    resellable_count: int


def analyze_non_unique_gifts_for_funding(all_gifts: List[SavedStarGift]) -> FundingAnalysis:
    """
    Best-effort check:
    - convertible gifts: have convert_stars > 0
    - resellable gifts: have can_resell_at <= now

    (Pricing/listing is a separate step; here we only detect possibility.)
    """
    now = int(time.time())
    convertible_count = 0
    resellable_count = 0

    for g in all_gifts:
        if isinstance(getattr(g, "gift", None), StarGiftUnique):
            continue

        convert_stars = getattr(g, "convert_stars", None)
        if isinstance(convert_stars, int) and convert_stars > 0:
            convertible_count += 1

        can_resell_at = getattr(g, "can_resell_at", None)
        if isinstance(can_resell_at, int) and can_resell_at <= now:
            resellable_count += 1

    return FundingAnalysis(convertible_count=convertible_count, resellable_count=resellable_count)








