import os

from server.config.load_env import load_env

load_env()


def get_bot_token() -> str:
    """
    Gets Telegram bot token from environment variable BOT_TOKEN.
    Raises RuntimeError if not set.
    """
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Get it from @BotFather on Telegram and set it in .env file or environment."
        )
    return token






