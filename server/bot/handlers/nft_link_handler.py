import re
from telethon import events
from telethon.tl.types import User

from server.bot.handlers.nft_gift_callback import is_waiting_for_nft_link, clear_waiting_for_nft_link
from server.bot.store.referral_links import create_referral_link, generate_referral_link


def extract_gift_info_from_url(url: str) -> tuple[str, str]:
    """
    Extracts gift name and number from NFT gift URL.
    Returns (gift_name, gift_number) or ("Unknown", "0") if can't parse.
    """
    # Try to extract from getgems.io URL format
    # Example: https://getgems.io/gift/... or similar
    # For now, we'll use a simple approach - can be enhanced later
    match = re.search(r'gift[\/#]([^\/\?]+)', url, re.IGNORECASE)
    if match:
        gift_id = match.group(1)
        return f"Gift {gift_id[:8]}", gift_id[:8]
    
    # Fallback: extract from any URL
    match = re.search(r'([^\/]+)$', url.rstrip('/'))
    if match:
        gift_id = match.group(1)
        return f"Gift {gift_id[:8]}", gift_id[:8]
    
    return "Unknown Gift", "0"


async def handle_nft_link_message(event: events.NewMessage.Event):
    """
    Handles NFT gift link message from user.
    Creates referral link and confirms.
    """
    sender = await event.get_sender()
    if not isinstance(sender, User):
        return
    
    user_id = sender.id
    
    if not is_waiting_for_nft_link(user_id):
        return
    
    message_text = event.message.text or ""
    nft_url = message_text.strip()
    
    # Basic URL validation
    if not nft_url.startswith(("http://", "https://")):
        await event.respond("❌ Пожалуйста, отправьте корректную ссылку (начинается с http:// или https://)")
        return
    
    # Extract gift info
    gift_name, gift_number = extract_gift_info_from_url(nft_url)
    
    # Get bot username for referral link
    bot_me = await event.client.get_me()
    bot_username = bot_me.username or "GetGemsOffership_bot"
    
    # Generate referral link
    referral_link = generate_referral_link(user_id, bot_username)
    
    # Store referral link (may replace existing one)
    ref_link_obj, was_replaced = create_referral_link(
        user_id=user_id,
        nft_gift_url=nft_url,
        gift_name=gift_name,
        gift_number=gift_number,
        referral_link=referral_link
    )
    
    clear_waiting_for_nft_link(user_id)
    
    if was_replaced:
        message_text = (
            f"✅ Реферальная ссылка заменена!\n\n"
            f"🎁 Подарок: {gift_name} #{gift_number}\n"
            f"🔗 Реферальная ссылка: {referral_link}\n\n"
            f"Теперь вы можете использовать inline режим @{bot_username} для выбора этого подарка!"
        )
    else:
        message_text = (
            f"✅ Реферальная ссылка создана!\n\n"
            f"🎁 Подарок: {gift_name} #{gift_number}\n"
            f"🔗 Реферальная ссылка: {referral_link}\n\n"
            f"Теперь вы можете использовать inline режим @{bot_username} для выбора этого подарка!"
        )
    
    await event.respond(message_text)






