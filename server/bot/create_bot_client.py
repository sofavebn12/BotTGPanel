from telethon import TelegramClient
from telethon.sessions import StringSession

from server.config.get_telegram_api_credentials import get_telegram_api_credentials


def create_bot_client() -> TelegramClient:
    """
    Creates a TelegramClient for the bot.
    Uses in-memory StringSession (no session file needed for bots).
    Note: For bots, we still need API credentials for Telethon initialization.
    Bot token is passed to client.start() method, not here.
    """
    api_id, api_hash = get_telegram_api_credentials()
    # Bots use StringSession, but still need API credentials
    return TelegramClient(StringSession(), api_id=api_id, api_hash=api_hash)


