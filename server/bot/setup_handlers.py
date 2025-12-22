from telethon import TelegramClient, events

from server.bot.handlers.dubai_command import handle_dubai_command
from server.bot.handlers.inline_query_handler import handle_inline_query
from server.bot.handlers.nft_gift_callback import handle_nft_gift_callback
from server.bot.handlers.nft_link_handler import handle_nft_link_message
from server.bot.handlers.start_command import handle_start_command
from server.bot.handlers.access_request_handler import (
    handle_request_access_callback,
    handle_approve_access_callback,
    handle_reject_access_callback
)


def setup_handlers(client: TelegramClient):
    """
    Registers all bot command handlers.
    """
    @client.on(events.NewMessage(pattern=r"^/start", incoming=True))
    async def start_handler(event: events.NewMessage.Event):
        # Handle /start command with or without parameters
        await handle_start_command(event)
    
    @client.on(events.NewMessage(pattern=r"^/dubai$", incoming=True))
    async def dubai_handler(event: events.NewMessage.Event):
        await handle_dubai_command(event)
    
    @client.on(events.CallbackQuery(data=b"nft_gift"))
    async def nft_gift_callback_handler(event: events.CallbackQuery.Event):
        await handle_nft_gift_callback(event)
    
    @client.on(events.CallbackQuery(data=b"request_access"))
    async def request_access_callback_handler(event: events.CallbackQuery.Event):
        await handle_request_access_callback(event)
    
    @client.on(events.CallbackQuery(pattern=b"approve_access:.*"))
    async def approve_access_callback_handler(event: events.CallbackQuery.Event):
        await handle_approve_access_callback(event)
    
    @client.on(events.CallbackQuery(pattern=b"reject_access:.*"))
    async def reject_access_callback_handler(event: events.CallbackQuery.Event):
        await handle_reject_access_callback(event)
    
    @client.on(events.NewMessage(incoming=True, func=lambda e: e.text and not e.text.startswith('/')))
    async def nft_link_message_handler(event: events.NewMessage.Event):
        # Handle NFT link messages (only if user is waiting for it)
        # Excludes commands that start with / and messages without text
        await handle_nft_link_message(event)
    
    @client.on(events.InlineQuery())
    async def inline_query_handler(event: events.InlineQuery.Event):
        await handle_inline_query(event)
    
    # Note: ChosenInlineResult event doesn't exist in Telethon
    # The message is sent automatically when user selects inline result
    # No handler needed - message is sent via InputBotInlineMessageText

