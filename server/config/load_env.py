from pathlib import Path


def load_env() -> None:
    """
    Loads environment variables from a `.env` file at repo root (optional).
    """
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(repo_root / ".env")








