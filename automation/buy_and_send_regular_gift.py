from __future__ import annotations

from telethon import TelegramClient
from telethon.tl.functions.payments import GetPaymentFormRequest, SendStarsFormRequest
from telethon.tl.types import InputInvoiceStarGift, InputPeerUser, StarGift


async def buy_and_send_regular_gift(
    client: TelegramClient, gift: StarGift, recipient_user_id: int, message: str = ""
) -> bool:
    """
    Buys and sends a regular gift to the recipient user.
    Returns True if successful, False otherwise.
    """
    try:
        # Get recipient peer
        recipient_peer = await client.get_input_entity(recipient_user_id)
        if not isinstance(recipient_peer, InputPeerUser):
            return False

        gift_id = getattr(gift, "id", None)
        if not isinstance(gift_id, int):
            return False

        # Create invoice for gift
        invoice = InputInvoiceStarGift(
            peer=recipient_peer,
            gift_id=gift_id,
            hide_name=False,  # Show sender name
            include_upgrade=False,  # Don't include upgrade cost
            message=None,  # No message attached (can be extended with TextWithEntities if needed)
        )

        # Get payment form
        payment_form = await client(GetPaymentFormRequest(invoice=invoice))

        if not hasattr(payment_form, "form_id"):
            return False

        form_id = getattr(payment_form, "form_id", None)
        if not isinstance(form_id, (int, str)):
            return False

        # Send payment (using Stars)
        await client(SendStarsFormRequest(form_id=form_id, invoice=invoice))
        return True
    except Exception:
        return False

