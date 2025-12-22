"""
Access control storage for bot users.
Manages which users have access to the bot.
"""
import json
import os
from typing import Set

# Path to access control file
ACCESS_CONTROL_FILE = os.path.join(
    os.path.dirname(__file__),
    "../../data/access_control.json"
)


def _load_access_data() -> dict:
    """Load access control data from file."""
    if not os.path.exists(ACCESS_CONTROL_FILE):
        return {
            "approved_users": [],
            "pending_requests": []
        }
    
    try:
        with open(ACCESS_CONTROL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ACCESS-CONTROL] Error loading access data: {e}")
        return {
            "approved_users": [],
            "pending_requests": []
        }


def _save_access_data(data: dict) -> None:
    """Save access control data to file."""
    try:
        os.makedirs(os.path.dirname(ACCESS_CONTROL_FILE), exist_ok=True)
        with open(ACCESS_CONTROL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ACCESS-CONTROL] Error saving access data: {e}")


def has_access(user_id: int) -> bool:
    """Check if user has access to the bot."""
    data = _load_access_data()
    return user_id in data.get("approved_users", [])


def grant_access(user_id: int) -> None:
    """Grant access to a user."""
    data = _load_access_data()
    if user_id not in data.get("approved_users", []):
        data["approved_users"].append(user_id)
        # Remove from pending requests if present
        if user_id in data.get("pending_requests", []):
            data["pending_requests"].remove(user_id)
        _save_access_data(data)
        print(f"[ACCESS-CONTROL] Granted access to user {user_id}")


def revoke_access(user_id: int) -> None:
    """Revoke access from a user."""
    data = _load_access_data()
    if user_id in data.get("approved_users", []):
        data["approved_users"].remove(user_id)
        _save_access_data(data)
        print(f"[ACCESS-CONTROL] Revoked access from user {user_id}")


def add_pending_request(user_id: int) -> bool:
    """
    Add a pending access request.
    Returns True if request was added, False if already pending.
    """
    data = _load_access_data()
    if user_id in data.get("pending_requests", []):
        return False  # Already pending
    
    data["pending_requests"].append(user_id)
    _save_access_data(data)
    print(f"[ACCESS-CONTROL] Added pending request for user {user_id}")
    return True


def remove_pending_request(user_id: int) -> None:
    """Remove a pending access request."""
    data = _load_access_data()
    if user_id in data.get("pending_requests", []):
        data["pending_requests"].remove(user_id)
        _save_access_data(data)
        print(f"[ACCESS-CONTROL] Removed pending request for user {user_id}")


def is_request_pending(user_id: int) -> bool:
    """Check if user has a pending access request."""
    data = _load_access_data()
    return user_id in data.get("pending_requests", [])
