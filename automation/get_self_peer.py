from telethon import TelegramClient


async def get_self_peer(client: TelegramClient):
    """
    Returns InputPeer for the current user.
    """
    return await client.get_input_entity("me")








