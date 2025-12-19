from telethon import TelegramClient

from server.config.load_env import load_env
from server.telethon.create_client import create_client


def get_telegram_client(user_id: str) -> TelegramClient:
    load_env()
    return create_client(user_id)








