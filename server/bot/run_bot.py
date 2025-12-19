import asyncio
import logging
import os
import sys

# Ensure repo root is on sys.path when running from server/bot/
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from server.bot.create_bot_client import create_bot_client
from server.bot.setup_handlers import setup_handlers

logger = logging.getLogger(__name__)


async def run_bot_async():
    """
    Starts the bot and runs it indefinitely.
    """
    from server.bot.get_bot_token import get_bot_token
    
    print("[BOT] Initializing bot...")
    try:
        bot_token = get_bot_token()
        print(f"[BOT] Bot token loaded (length: {len(bot_token)})")
    except Exception as e:
        print(f"[BOT] [ERROR] Failed to get bot token: {str(e)}")
        raise
    
    print("[BOT] Creating Telegram client...")
    try:
        client = create_bot_client()
        print("[BOT] Client created successfully")
    except Exception as e:
        print(f"[BOT] [ERROR] Failed to create client: {str(e)}")
        raise
    
    print("[BOT] Connecting to Telegram...")
    try:
        await client.start(bot_token=bot_token)
        print("[BOT] Connected to Telegram successfully")
    except Exception as e:
        # Не ждём FloodWait и не делаем автоповторы — пусть падает, а ты сам решаешь, когда перезапускать
        print(f"[BOT] [ERROR] Failed to connect: {str(e)}")
        import traceback
        print(f"[BOT] [ERROR] Traceback: {traceback.format_exc()}")
        raise
    
    print("[BOT] Setting up handlers...")
    setup_handlers(client)
    print("[BOT] Handlers registered")
    
    me = await client.get_me()
    print(f"[BOT] Bot started successfully! Bot username: @{me.username}")
    print("[BOT] Bot is ready to receive messages. Press Ctrl+C to stop.")
    
    await client.run_until_disconnected()


def run_bot():
    """
    Entry point to run the bot (blocking).
    """
    print("[BOT] Starting bot process...")
    try:
        asyncio.run(run_bot_async())
    except KeyboardInterrupt:
        print("\n[BOT] Bot stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"[BOT] [ERROR] Bot crashed: {str(e)}")
        import traceback
        print(f"[BOT] [ERROR] Traceback: {traceback.format_exc()}")
        raise

