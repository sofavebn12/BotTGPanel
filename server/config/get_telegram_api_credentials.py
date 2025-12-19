import os


def get_telegram_api_credentials() -> tuple[int, str]:
    """
    Reads Telegram API credentials from environment variables:
      - TG_API_ID
      - TG_API_HASH
    """
    api_id_raw = os.environ.get("TG_API_ID", "").strip()
    api_hash = os.environ.get("TG_API_HASH", "").strip()

    if not api_id_raw or not api_hash:
        raise RuntimeError("Missing TG_API_ID/TG_API_HASH env vars")

    try:
        api_id = int(api_id_raw)
    except ValueError as e:
        raise RuntimeError("TG_API_ID must be an integer") from e

    return api_id, api_hash








