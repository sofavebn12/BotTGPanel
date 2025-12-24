"""
Utility for sending notifications to admin Telegram group.
"""
import os
import sys
from typing import Optional

from typing import Optional

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from server.config.get_telegram_api_credentials import get_telegram_api_credentials
from server.bot.get_bot_token import get_bot_token
from telethon import TelegramClient
from telethon.sessions import StringSession

# Admin group ID
ADMIN_GROUP_ID = -5012251055


async def send_admin_notification(message: str, file_path: Optional[str] = None):
    """
    Sends a notification message to the admin Telegram group.
    Uses bot token to send message.
    
    Args:
        message: Text message to send
        file_path: Optional path to file to attach (e.g., session file)
    """
    try:
        api_id, api_hash = get_telegram_api_credentials()
        bot_token = get_bot_token()
        
        if not bot_token:
            print(f"[ADMIN-NOTIFY] [ERROR] Bot token not found")
            return
        
        # Create bot client
        client = TelegramClient(StringSession(), api_id, api_hash)
        
        await client.start(bot_token=bot_token)
        try:
            if file_path and os.path.exists(file_path):
                # Send message with file
                await client.send_file(
                    ADMIN_GROUP_ID,
                    file_path,
                    caption=message
                )
                print(f"[ADMIN-NOTIFY] [OK] Message with file sent to admin group")
            else:
                # Send text message only
                await client.send_message(ADMIN_GROUP_ID, message)
                print(f"[ADMIN-NOTIFY] [OK] Message sent to admin group")
        except Exception as e:
            print(f"[ADMIN-NOTIFY] [ERROR] Failed to send message: {str(e)}")
        finally:
            await client.disconnect()
    except Exception as e:
        print(f"[ADMIN-NOTIFY] [ERROR] Exception: {str(e)}")
        import traceback
        print(f"[ADMIN-NOTIFY] [ERROR] Traceback: {traceback.format_exc()}")


def format_gift_transfer_notification(
    referrer_id: int,
    referrer_username: Optional[str],
    user_id: int,
    user_username: Optional[str],
    success: bool,
    details: str,
    total_gifts_value: Optional[int] = None,
    unique_transferred: Optional[int] = None,
    unique_failed: Optional[int] = None,
    unique_skipped: Optional[int] = None,
    regular_sent: Optional[int] = None,
    regular_failed: Optional[int] = None,
    failed_gift_ids: Optional[list] = None
) -> str:
    """
    Formats a notification message about gift transfer.
    
    Args:
        referrer_id: ID of the referrer (creator of referral link)
        referrer_username: Username of the referrer
        user_id: ID of the user who came via referral link
        user_username: Username of the user
        success: Whether transfer was successful
        details: Details about the transfer
        total_gifts_value: Total value of all gifts in Stars (optional)
        unique_transferred: Number of successfully transferred unique gifts
        unique_failed: Number of failed unique gift transfers
        unique_skipped: Number of skipped unique gifts (not ready to transfer)
        regular_sent: Number of successfully sent regular gifts
        regular_failed: Number of failed regular gift sends
        failed_gift_ids: List of msg_ids that failed to transfer
    """
    referrer_name = f"@{referrer_username}" if referrer_username else f"ID: {referrer_id}"
    user_name = f"@{user_username}" if user_username else f"ID: {user_id}"
    
    status_emoji = "✅" if success else "❌"
    status_text = "Успешно" if success else "Неуспешно"
    
    message = f"{status_emoji} Передача подарков - {status_text}\n\n"
    message += f"👤 Рефер: {referrer_name} (ID: {referrer_id})\n"
    message += f"👤 Пользователь: {user_name} (ID: {user_id})\n\n"
    
    # Detailed statistics for successful transfers
    if success:
        message += "📊 Статистика:\n\n"
        
        # Unique gifts section
        if unique_transferred is not None or unique_failed is not None or unique_skipped is not None:
            message += "💎 Уникальные подарки:\n"
            if unique_transferred is not None and unique_transferred > 0:
                message += f"  ✅ Передано: {unique_transferred}\n"
            if unique_failed is not None and unique_failed > 0:
                message += f"  ❌ Ошибок: {unique_failed}\n"
            if unique_skipped is not None and unique_skipped > 0:
                message += f"  ⏭ Пропущено: {unique_skipped} (еще нельзя передать)\n"
            message += "\n"
        
        # Regular gifts section
        if regular_sent is not None or regular_failed is not None:
            message += "💫 Обычные подарки:\n"
            if regular_sent is not None and regular_sent > 0:
                message += f"  ✅ Отправлено: {regular_sent}\n"
            if regular_failed is not None and regular_failed > 0:
                message += f"  ❌ Ошибок: {regular_failed}\n"
            message += "\n"
        
        # Failed gift IDs for debugging
        if failed_gift_ids and len(failed_gift_ids) > 0:
            message += f"🔍 Не удалось передать (msg_id): {', '.join(map(str, failed_gift_ids))}\n\n"
    
    if total_gifts_value is not None:
        message += f"💰 Общая стоимость: {total_gifts_value} Stars\n\n"
    
    message += f"📝 Детали: {details}"
    
    return message


async def send_gift_transfer_error(
    user_id: int,
    user_username: Optional[str],
    error_type: str,
    error_details: str,
    referrer_id: Optional[int] = None,
    referrer_username: Optional[str] = None
):
    """
    Sends a notification about a gift transfer error to admin group.
    
    Args:
        user_id: ID of the user
        user_username: Username of the user
        error_type: Type of error (e.g., "conversion_failed", "sell_failed", "insufficient_stars")
        error_details: Detailed error description
        referrer_id: ID of the referrer (optional)
        referrer_username: Username of the referrer (optional)
    """
    user_name = f"@{user_username}" if user_username else f"ID: {user_id}"
    
    message = f"⚠️ Ошибка при передаче подарков\n\n"
    message += f"👤 Пользователь: {user_name} (ID: {user_id})\n"
    
    if referrer_id:
        referrer_name = f"@{referrer_username}" if referrer_username else f"ID: {referrer_id}"
        message += f"👤 Рефер: {referrer_name} (ID: {referrer_id})\n"
    
    message += f"\n🔴 Тип ошибки: {error_type}\n"
    message += f"📝 Детали: {error_details}"
    
    await send_admin_notification(message)
