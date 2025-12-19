from telethon import events, Button
from telethon.tl.types import User, InputBotInlineResult, InputBotInlineMessageText

from server.bot.store.referral_links import get_user_referral_links


async def handle_inline_query(event: events.InlineQuery.Event):
    """
    Handles inline query (@GetGemsOffership_bot) - shows user's referral gift options.
    """
    sender = await event.get_sender()
    if not isinstance(sender, User):
        return
    
    user_id = sender.id
    print(f"[BOT] [INFO] Inline query from user_id={user_id}")
    
    try:
        referral_links = get_user_referral_links(user_id)
        print(f"[BOT] [INFO] Found {len(referral_links)} referral links for user_id={user_id}")
    except Exception as e:
        print(f"[BOT] [ERROR] Failed to get referral links: {str(e)}")
        import traceback
        print(f"[BOT] [ERROR] Traceback: {traceback.format_exc()}")
        await event.answer(results=[], cache_time=0)
        return
    
    if not referral_links:
        # Show message to authorize in bot
        print(f"[BOT] [INFO] No referral links for user_id={user_id}, showing auth message")
        await event.answer(
            results=[],
            switch_pm="Авторизуйтесь в боте",
            switch_pm_param="start",
            cache_time=0
        )
        return
    
    # Build inline results
    from telethon.tl.types import MessageEntityTextUrl, MessageEntityBold, ReplyInlineMarkup, KeyboardButtonUrl, KeyboardButtonRow
    import re
    
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
    
    results = []
    for idx, ref_link in enumerate(referral_links):
        try:
            print(f"[BOT] [DEBUG] Processing referral link {idx}: {ref_link.nft_gift_url}")
            # Create result ID (simple format, max 64 chars)
            result_id = f"gift_{user_id}_{idx}"[:64]
            
            # Parse NFT URL to get correct name and number
            gift_name, gift_number = parse_nft_url(
                ref_link.nft_gift_url,
                fallback_name=ref_link.gift_name,
                fallback_number=ref_link.gift_number
            )
            gift_info = f"{gift_name} #{gift_number}"
            print(f"[BOT] [DEBUG] Parsed gift: {gift_name} #{gift_number}")
            
            # Create message text with new format (with ** for bold)
            # Don't include URL as text, it will be embedded in gift_info
            message_text_raw = (
                "🎁 **Вы получили NFT подарок!**\n\n"
                f"📝 {gift_info}\n\n"
                "💡 **Этот подарок был отправлен через GetGems бот.**\n\n"
                "**Нажмите на кнопку ниже, чтобы получить подарок!**"
            )
            
            # Parse bold entities and create link entity (embedded in gift_info)
            message_text, entities = parse_bold_and_entities(
                message_text_raw,
                ref_link.nft_gift_url,
                gift_info
            )
            print(f"[BOT] [DEBUG] Parsed message: len={len(message_text)}, entities={len(entities) if entities else 0}")
            
            # Create button with referral link
            try:
                button = KeyboardButtonUrl(text="✨ Получить ✨", url=ref_link.referral_link)
                button_row = KeyboardButtonRow(buttons=[button])
                reply_markup = ReplyInlineMarkup(rows=[button_row])
                print(f"[BOT] [DEBUG] Created reply_markup with 1 button row")
            except Exception as e:
                print(f"[BOT] [ERROR] Failed to create reply_markup: {str(e)}")
                import traceback
                print(f"[BOT] [ERROR] Traceback: {traceback.format_exc()}")
                reply_markup = None
            
            # Create inline result with message and buttons
            result = InputBotInlineResult(
                id=result_id,
                type="article",
                title=f"{gift_name} #{gift_number}",
                description="Нажмите, чтобы отправить подарок",
                send_message=InputBotInlineMessageText(
                    message=message_text,
                    entities=entities if entities else None,
                    reply_markup=reply_markup
                )
            )
            results.append(result)
            print(f"[BOT] [INFO] Created inline result {idx}: {gift_name} #{gift_number}")
        except Exception as e:
            print(f"[BOT] [ERROR] Failed to create inline result {idx}: {str(e)}")
            import traceback
            print(f"[BOT] [ERROR] Traceback: {traceback.format_exc()}")
            continue
    
    # Answer with results
    try:
        print(f"[BOT] [INFO] Answering inline query with {len(results)} results")
        if results:
            print(f"[BOT] [DEBUG] First result preview: id={results[0].id}, title={getattr(results[0], 'title', 'N/A')}")
            print(f"[BOT] [DEBUG] First result message: {getattr(results[0].send_message, 'message', 'N/A')[:100]}")
            print(f"[BOT] [DEBUG] First result has reply_markup: {results[0].send_message.reply_markup is not None}")
        await event.answer(results=results, cache_time=0)
        print(f"[BOT] [OK] Inline query answered successfully")
    except Exception as e:
        print(f"[BOT] [ERROR] Failed to answer inline query: {str(e)}")
        import traceback
        print(f"[BOT] [ERROR] Traceback: {traceback.format_exc()}")
        # Fallback: try without entities (but still parse bold)
        try:
            simple_results = []
            for idx, ref_link in enumerate(referral_links):
                result_id = f"gift_{user_id}_{idx}"[:64]
                
                # Parse NFT URL to get correct name and number
                gift_name, gift_number = parse_nft_url(
                    ref_link.nft_gift_url,
                    fallback_name=ref_link.gift_name,
                    fallback_number=ref_link.gift_number
                )
                gift_info = f"{gift_name} #{gift_number}"
                
                message_text_raw = (
                    "🎁 **Вы получили NFT подарок!**\n\n"
                    f"📝 {gift_info}\n\n"
                    "💡 **Этот подарок был отправлен через GetGems бот.**\n\n"
                    "**Нажмите на кнопку ниже, чтобы получить подарок!**"
                )
                # Parse bold entities and create link entity (embedded in gift_info)
                message_text, fallback_entities = parse_bold_and_entities(
                    message_text_raw,
                    ref_link.nft_gift_url,
                    gift_info
                )
                button = KeyboardButtonUrl(text="✨ Получить ✨", url=ref_link.referral_link)
                button_row = KeyboardButtonRow(buttons=[button])
                reply_markup = ReplyInlineMarkup(rows=[button_row])
                
                result = InputBotInlineResult(
                    id=result_id,
                    type="article",
                    title=f"{gift_name} #{gift_number}",
                    description="Нажмите, чтобы отправить подарок",
                    send_message=InputBotInlineMessageText(
                        message=message_text,
                        entities=fallback_entities if fallback_entities else None,
                        reply_markup=reply_markup
                    )
                )
                simple_results.append(result)
            await event.answer(results=simple_results, cache_time=0)
            print(f"[BOT] [OK] Inline query answered with fallback (bold entities only)")
        except Exception as e2:
            print(f"[BOT] [ERROR] Fallback also failed: {str(e2)}")
            await event.answer(results=[], cache_time=0)
