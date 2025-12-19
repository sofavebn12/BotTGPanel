import os
import sys
import argparse
import asyncio

# Ensure repo root is on sys.path when running as a script
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from automation.analyze_non_unique_gifts_for_funding import analyze_non_unique_gifts_for_funding
from automation.calc_required_transfer_stars import calc_required_transfer_stars
from automation.filter_unique_star_gifts import filter_unique_star_gifts
from automation.get_saved_star_gifts import get_saved_star_gifts
from automation.get_self_peer import get_self_peer
from automation.get_stars_balance import get_stars_balance
from automation.get_telegram_client import get_telegram_client


async def _main_async(user_id: str, limit: int) -> int:
    client = get_telegram_client(user_id)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            print(f"[ERROR] Session for user_id={user_id} is not authorized.")
            return 2

        me = await get_self_peer(client)
        gifts = await get_saved_star_gifts(client=client, peer=me, limit=limit)
        unique = filter_unique_star_gifts(gifts)

        stars_balance = await get_stars_balance(client=client, peer=me)
        required_transfer = calc_required_transfer_stars(unique)

        print(f"User: {user_id}")
        print(f"Saved gifts total: {len(gifts)}")
        print(f"Unique (NFT) gifts: {len(unique)}")
        print(f"Stars balance: {stars_balance}")
        print(f"Stars required to transfer all transferable unique gifts: {required_transfer}")

        if len(unique) == 0:
            return 0

        if stars_balance >= required_transfer:
            print("[OK] Enough Stars to transfer unique gifts.")
            return 0

        shortage = required_transfer - stars_balance
        print(f"[WARN] Not enough Stars. Shortage: {shortage}")

        funding = analyze_non_unique_gifts_for_funding(gifts)
        print(f"Non-unique gifts convertible to Stars: {funding.convertible_count}")
        print(f"Non-unique gifts potentially resellable now: {funding.resellable_count}")
        print(
            "Next step: implement conversion (payments.convertStarGift) and/or listing for resale "
            "(payments.updateStarGiftPrice) with chosen pricing strategy."
        )
        return 0
    finally:
        await client.disconnect()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True, help="Session key (maps to data/sessions/<user-id>.session)")
    parser.add_argument("--limit", type=int, default=200, help="Max gifts to fetch")
    args = parser.parse_args()

    return asyncio.run(_main_async(user_id=args.user_id, limit=args.limit))


if __name__ == "__main__":
    raise SystemExit(main())


