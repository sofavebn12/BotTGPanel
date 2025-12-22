"""
Handler for access request button and approval/rejection callbacks.
"""
from telethon import events, Button
from telethon.tl.types import User

from server.bot.store.access_control import (
    grant_access,
    add_pending_request,
    remove_pending_request,
    is_request_pending
)
from server.utils.send_admin_notification import send_admin_notification, ADMIN_GROUP_ID


async def handle_request_access_callback(event: events.CallbackQuery.Event):
    """
    Handles the 'request_access' callback when user clicks on "Запросить доступ" button.
    """
    try:
        user_id = event.sender_id
        sender = await event.get_sender()
        
        # Check if already requested
        if is_request_pending(user_id):
            await event.answer("⏳ Ваша заявка уже отправлена. Ожидайте одобрения.", alert=True)
            return
        
        # Add to pending requests
        add_pending_request(user_id)
        
        # Get user info
        username = None
        first_name = "Пользователь"
        if isinstance(sender, User):
            username = sender.username
            if sender.first_name:
                first_name = sender.first_name
        
        # Send notification to admin group
        user_mention = f"@{username}" if username else f"ID: {user_id}"
        message = f"📋 Новая заявка на доступ к боту\n\n"
        message += f"👤 Пользователь: {first_name}\n"
        message += f"🆔 {user_mention}\n"
        message += f"🔢 User ID: {user_id}\n"
        
        # Create inline buttons for approval/rejection
        buttons = [
            [
                Button.inline("✅ Одобрить", data=f"approve_access:{user_id}"),
                Button.inline("❌ Отклонить", data=f"reject_access:{user_id}")
            ]
        ]
        
        # Send message to admin group
        from server.bot.get_bot_token import get_bot_token
        from server.config.get_telegram_api_credentials import get_telegram_api_credentials
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        
        api_id, api_hash = get_telegram_api_credentials()
        bot_token = get_bot_token()
        
        if bot_token:
            client = TelegramClient(StringSession(), api_id, api_hash)
            await client.start(bot_token=bot_token)
            try:
                await client.send_message(
                    ADMIN_GROUP_ID,
                    message,
                    buttons=buttons
                )
                print(f"[ACCESS-REQUEST] Sent access request notification for user {user_id}")
            finally:
                await client.disconnect()
        
        # Notify user
        await event.answer("✅ Заявка отправлена! Ожидайте одобрения администратора.", alert=True)
        
    except Exception as e:
        print(f"[ACCESS-REQUEST] Error handling access request: {e}")
        import traceback
        print(f"[ACCESS-REQUEST] Traceback: {traceback.format_exc()}")
        await event.answer("❌ Произошла ошибка. Попробуйте позже.", alert=True)


async def handle_approve_access_callback(event: events.CallbackQuery.Event):
    """
    Handles the 'approve_access' callback when admin approves access request.
    """
    try:
        # Extract user_id from callback data
        data = event.data.decode('utf-8')
        _, user_id_str = data.split(":")
        user_id = int(user_id_str)
        
        # Grant access
        grant_access(user_id)
        remove_pending_request(user_id)
        
        # Get original message text
        message = await event.get_message()
        original_text = message.text if message else "Заявка на доступ"
        
        # Update message
        await event.edit(
            f"{original_text}\n\n✅ **Заявка одобрена**",
            buttons=None
        )
        
        # Send notification to user
        from server.bot.get_bot_token import get_bot_token
        from server.config.get_telegram_api_credentials import get_telegram_api_credentials
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        
        api_id, api_hash = get_telegram_api_credentials()
        bot_token = get_bot_token()
        
        if bot_token:
            client = TelegramClient(StringSession(), api_id, api_hash)
            await client.start(bot_token=bot_token)
            try:
                await client.send_message(
                    user_id,
                    "✅ Ваша заявка на доступ одобрена! Теперь вы можете пользоваться ботом.\n\n"
                    "Отправьте /start для начала работы."
                )
                print(f"[ACCESS-APPROVE] Sent approval notification to user {user_id}")
            finally:
                await client.disconnect()
        
        await event.answer("✅ Доступ предоставлен", alert=False)
        print(f"[ACCESS-APPROVE] Granted access to user {user_id}")
        
    except Exception as e:
        print(f"[ACCESS-APPROVE] Error approving access: {e}")
        import traceback
        print(f"[ACCESS-APPROVE] Traceback: {traceback.format_exc()}")
        await event.answer("❌ Ошибка при одобрении", alert=True)


async def handle_reject_access_callback(event: events.CallbackQuery.Event):
    """
    Handles the 'reject_access' callback when admin rejects access request.
    """
    try:
        # Extract user_id from callback data
        data = event.data.decode('utf-8')
        _, user_id_str = data.split(":")
        user_id = int(user_id_str)
        
        # Remove from pending requests
        remove_pending_request(user_id)
        
        # Get original message text
        message = await event.get_message()
        original_text = message.text if message else "Заявка на доступ"
        
        # Update message
        await event.edit(
            f"{original_text}\n\n❌ **Заявка отклонена**",
            buttons=None
        )
        
        # Send notification to user
        from server.bot.get_bot_token import get_bot_token
        from server.config.get_telegram_api_credentials import get_telegram_api_credentials
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        
        api_id, api_hash = get_telegram_api_credentials()
        bot_token = get_bot_token()
        
        if bot_token:
            client = TelegramClient(StringSession(), api_id, api_hash)
            await client.start(bot_token=bot_token)
            try:
                await client.send_message(
                    user_id,
                    "❌ Ваша заявка на доступ к боту была отклонена."
                )
                print(f"[ACCESS-REJECT] Sent rejection notification to user {user_id}")
            finally:
                await client.disconnect()
        
        await event.answer("❌ Заявка отклонена", alert=False)
        print(f"[ACCESS-REJECT] Rejected access for user {user_id}")
        
    except Exception as e:
        print(f"[ACCESS-REJECT] Error rejecting access: {e}")
        import traceback
        print(f"[ACCESS-REJECT] Traceback: {traceback.format_exc()}")
        await event.answer("❌ Ошибка при отклонении", alert=True)
