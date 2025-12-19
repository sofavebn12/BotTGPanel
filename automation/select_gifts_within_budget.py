from __future__ import annotations

from typing import List

from telethon.tl.types import StarGift


def select_gifts_within_budget(gifts: List[StarGift], budget_stars: int) -> List[StarGift]:
    """
    Selects gifts that can be bought within the budget, prioritizing cheaper gifts.
    Returns list of gifts sorted by price (ascending) that fit within budget.
    """
    affordable: List[StarGift] = []
    total_cost = 0

    # Sort gifts by price (stars) ascending
    sorted_gifts = sorted(gifts, key=lambda g: getattr(g, "stars", 0) or 0)

    for gift in sorted_gifts:
        stars = getattr(gift, "stars", None)
        if not isinstance(stars, int) or stars <= 0:
            continue

        if total_cost + stars <= budget_stars:
            affordable.append(gift)
            total_cost += stars

    return affordable






