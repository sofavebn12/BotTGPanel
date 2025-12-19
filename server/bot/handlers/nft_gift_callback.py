from telethon import events
from telethon.tl.types import User

# Store user_id -> waiting for NFT link
_waiting_for_nft_link: dict[int, bool] = {}


async def handle_nft_gift_callback(event: events.CallbackQuery.Event):
    """
    Handles NFT Gift button click - asks user to send NFT gift link.
    """
    sender = await event.get_sender()
    if not isinstance(sender, User):
        await event.answer("Error: Could not identify user")
        return
    
    user_id = sender.id
    _waiting_for_nft_link[user_id] = True
    
    await event.answer("Пожалуйста, отправьте ссылку на NFT подарок")
    await event.edit("Пожалуйста, отправьте ссылку на NFT подарок")


def is_waiting_for_nft_link(user_id: int) -> bool:
    """Checks if user is waiting to provide NFT gift link."""
    return _waiting_for_nft_link.get(user_id, False)


def clear_waiting_for_nft_link(user_id: int):
    """Clears waiting state for user."""
    _waiting_for_nft_link.pop(user_id, None)






