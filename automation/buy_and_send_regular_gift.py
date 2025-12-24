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
    gift_id = getattr(gift, "id", None)
    gift_title = getattr(gift, "title", None) or f"Gift #{gift_id}"
    
    try:
        # Get recipient peer
        recipient_peer = await client.get_input_entity(recipient_user_id)
        if not isinstance(recipient_peer, InputPeerUser):
            print(f"[ERROR] Invalid recipient peer type for user_id={recipient_user_id}")
            return False

        if not isinstance(gift_id, int):
            print(f"[ERROR] Invalid gift_id: {gift_id}")
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
            print(f"[ERROR] Payment form has no form_id for gift: {gift_title}")
            return False

        form_id = getattr(payment_form, "form_id", None)
        if not isinstance(form_id, (int, str)):
            print(f"[ERROR] Invalid form_id type: {type(form_id)} for gift: {gift_title}")
            return False

        # Send payment (using Stars)
        await client(SendStarsFormRequest(form_id=form_id, invoice=invoice))
        return True
    except Exception as e:
        print(f"[ERROR] Failed to buy/send gift {gift_title}: {type(e).__name__}: {str(e)}")
        return False

