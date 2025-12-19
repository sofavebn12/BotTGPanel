import re
from pathlib import Path

from server.session_storage.get_session_dir import get_session_dir


def get_session_file_base(user_id: str) -> Path:
    """
    Returns a filesystem path *without extension* for Telethon SQLiteSession.
    Telethon will create: <base>.session (and journal files).
    """
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", user_id.strip()) or "user"
    session_dir = get_session_dir()
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir / safe








