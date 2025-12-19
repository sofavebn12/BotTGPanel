from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class AuthState:
    user_id: str
    phone_number: str
    phone_code_hash: Optional[str] = None
    session_string: str = ""
    is_authorized: bool = False


_STATE: Dict[str, AuthState] = {}


def get_auth_state(user_id: str) -> Optional[AuthState]:
    return _STATE.get(user_id)


def upsert_auth_state(state: AuthState) -> None:
    _STATE[state.user_id] = state


def clear_auth_state(user_id: str) -> None:
    _STATE.pop(user_id, None)








