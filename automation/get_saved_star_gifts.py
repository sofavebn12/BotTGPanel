from typing import List

from telethon import TelegramClient
from telethon.tl.functions.payments import GetSavedStarGiftsRequest
from telethon.tl.types import SavedStarGift


async def get_saved_star_gifts(
    *,
    client: TelegramClient,
    peer,
    limit: int = 200,
) -> List[SavedStarGift]:
    """
    Fetch user's saved/owned star gifts (includes unique gifts/NFTs unless excluded).

    Note: MTProto uses an opaque `offset` string for paging.
    """
    out: List[SavedStarGift] = []
    offset = ""

    while len(out) < limit:
        page = await client(
            GetSavedStarGiftsRequest(
                peer=peer,
                offset=offset,
                limit=min(100, limit - len(out)),
            )
        )

        # Telethon objects usually expose `gifts` and optional `next_offset`
        gifts = getattr(page, "gifts", None) or []
        out.extend(gifts)

        next_offset = getattr(page, "next_offset", None)
        if not next_offset:
            break
        offset = next_offset

    return out








