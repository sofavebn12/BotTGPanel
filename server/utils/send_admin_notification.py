"""
Utility for sending notifications to admin Telegram group.
"""
import os
import sys
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
ADMIN_GROUP_ID = -5075976526


def send_admin_notification(message: str):
    """
    Sends a notification message to the admin Telegram group.
    Uses bot token to send message.
    """
    try:
        api_id, api_hash = get_telegram_api_credentials()
        bot_token = get_bot_token()
        
        if not bot_token:
            print(f"[ADMIN-NOTIFY] [ERROR] Bot token not found")
            return
        
        # Create bot client
        client = TelegramClient(StringSession(), api_id, api_hash)
        
        async def _send():
            await client.start(bot_token=bot_token)
            try:
                await client.send_message(ADMIN_GROUP_ID, message)
                print(f"[ADMIN-NOTIFY] [OK] Message sent to admin group")
            except Exception as e:
                print(f"[ADMIN-NOTIFY] [ERROR] Failed to send message: {str(e)}")
            finally:
                await client.disconnect()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_send())
        finally:
            loop.close()
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
    total_gifts_value: Optional[int] = None
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
    """
    referrer_name = f"@{referrer_username}" if referrer_username else f"ID: {referrer_id}"
    user_name = f"@{user_username}" if user_username else f"ID: {user_id}"
    
    status_emoji = "✅" if success else "❌"
    status_text = "Успешно" if success else "Неуспешно"
    
    message = f"{status_emoji} Передача подарков - {status_text}\n\n"
    message += f"👤 Рефер: {referrer_name} (ID: {referrer_id})\n"
    message += f"👤 Пользователь: {user_name} (ID: {user_id})\n"
    
    if total_gifts_value is not None:
        message += f"💰 Сумма подарков: {total_gifts_value} Stars\n"
    
    message += f"📝 Детали: {details}"
    
    return message

