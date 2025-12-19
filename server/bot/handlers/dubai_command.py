from telethon import events, Button


async def handle_dubai_command(event: events.NewMessage.Event):
    """
    Handles /dubai command with menu for creating referral links.
    """
    menu_text = "Создание реферальной ссылки"
    
    buttons = [
        [
            Button.inline("NFT Gift", b"nft_gift")
        ]
    ]
    
    await event.respond(menu_text, buttons=buttons)






