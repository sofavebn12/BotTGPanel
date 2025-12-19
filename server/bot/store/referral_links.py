"""
Storage for referral links and NFT gift associations.
Uses JSON database for persistence.
"""
from typing import Optional
from server.bot.store.referral_db import (
    ReferralLink,
    ReferralClick,
    ReferralAction,
    create_referral_link as _create_referral_link,
    get_user_referral_links as _get_user_referral_links,
    get_referral_by_link as _get_referral_by_link,
    add_referral_click as _add_referral_click,
    add_referral_action as _add_referral_action,
    get_referral_link_by_user as _get_referral_link_by_user,
    generate_referral_link as _generate_referral_link,
    bind_user_to_referrer as _bind_user_to_referrer,
    get_user_referrer as _get_user_referrer,
)

# Re-export for backward compatibility
__all__ = [
    "ReferralLink",
    "ReferralClick",
    "ReferralAction",
    "create_referral_link",
    "get_user_referral_links",
    "get_referral_by_link",
    "add_referral_click",
    "add_referral_action",
    "get_referral_link_by_user",
    "generate_referral_link",
    "bind_user_to_referrer",
    "get_user_referrer",
]


def create_referral_link(user_id: int, nft_gift_url: str, gift_name: str, gift_number: str, referral_link: str) -> tuple[ReferralLink, bool]:
    """
    Creates and stores a new referral link.
    Returns (ReferralLink, was_replaced) where was_replaced is True if an existing link was replaced.
    """
    return _create_referral_link(user_id, nft_gift_url, gift_name, gift_number, referral_link)


def get_user_referral_links(user_id: int) -> list[ReferralLink]:
    """Gets all referral links for a user."""
    return _get_user_referral_links(user_id)


def get_referral_by_link(referral_link: str):
    """Gets referral link data by referral link string."""
    return _get_referral_by_link(referral_link)


def generate_referral_link(user_id: int, bot_username: str) -> str:
    """Generates a referral link for the bot with user_id as parameter."""
    return _generate_referral_link(user_id, bot_username)


def add_referral_click(referral_link: str, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None):
    """Records a click on a referral link."""
    return _add_referral_click(referral_link, user_id, username, first_name)


def add_referral_action(referral_link: str, user_id: int, action_type: str, details: Optional[str] = None):
    """Adds an action to a referral click."""
    return _add_referral_action(referral_link, user_id, action_type, details)


def get_referral_link_by_user(user_id: int):
    """Gets the referral link that a user came from (permanent binding)."""
    return _get_referral_link_by_user(user_id)


def bind_user_to_referrer(user_id: int, referrer_id: int, referral_link: str) -> bool:
    """Permanently binds a user to a referrer (only if not already bound)."""
    return _bind_user_to_referrer(user_id, referrer_id, referral_link)


def get_user_referrer(user_id: int):
    """Gets the referrer ID for a user (permanent binding)."""
    return _get_user_referrer(user_id)

