from telethon import TelegramClient

from server.config.get_telegram_api_credentials import get_telegram_api_credentials
from server.session_storage.get_session_file_base import get_session_file_base


def create_client(user_id: str) -> TelegramClient:
    api_id, api_hash = get_telegram_api_credentials()
    session_base = get_session_file_base(user_id)
    # Passing a path without extension -> Telethon will create "<path>.session"
    return TelegramClient(str(session_base), api_id, api_hash)


