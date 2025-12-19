from typing import List

from telethon.tl.types import SavedStarGift, StarGiftUnique


def filter_unique_star_gifts(gifts: List[SavedStarGift]) -> List[SavedStarGift]:
    """
    Unique gifts (collectible/NFT) are represented as StarGiftUnique in SavedStarGift.gift.
    """
    out: List[SavedStarGift] = []
    for g in gifts:
        if isinstance(getattr(g, "gift", None), StarGiftUnique):
            out.append(g)
    return out








