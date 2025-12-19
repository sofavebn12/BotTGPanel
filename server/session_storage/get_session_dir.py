from pathlib import Path


def get_session_dir() -> Path:
    """
    Folder where Telethon SQLite sessions (*.session) are stored.
    """
    # repo_root/data/sessions
    return Path(__file__).resolve().parents[2] / "data" / "sessions"








