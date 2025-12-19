from telethon import TelegramClient
from telethon.tl.functions.payments import GetStarsStatusRequest


async def get_stars_balance(*, client: TelegramClient, peer) -> int:
    """
    Returns current Stars balance as integer Stars (best-effort).
    """
    status = await client(GetStarsStatusRequest(peer=peer))

    # Common fields observed in TL objects:
    # - balance: int
    # - balance: StarsAmount(amount, nanos)
    balance = getattr(status, "balance", None)
    if balance is None:
        # fallback: some schemas use `stars` or `current_balance`
        for k in ("stars", "current_balance"):
            v = getattr(status, k, None)
            if v is not None:
                balance = v
                break

    if isinstance(balance, int):
        return balance

    amount = getattr(balance, "amount", None)
    if isinstance(amount, int):
        return amount

    return 0








