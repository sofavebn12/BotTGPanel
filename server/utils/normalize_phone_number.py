import re


def normalize_phone_number(raw: str) -> str:
    """
    Normalizes a phone number into a best-effort E.164-like format.

    Accepts:
      - "+358 46 551 4599"
      - "00358 46 551 4599"
      - "358465514599"
      - "++358465514599"

    Returns:
      - "+358465514599"
    """
    if raw is None:
        return ""

    s = str(raw).strip()
    if not s:
        return ""

    # Convert international dialing prefix 00 -> +
    if s.startswith("00"):
        s = "+" + s[2:]

    # Remove all characters except digits and '+'
    s = re.sub(r"[^\d+]", "", s)

    # Keep only one leading '+', remove any later '+'
    if s.startswith("+"):
        s = "+" + re.sub(r"\+", "", s[1:])
    else:
        s = re.sub(r"\+", "", s)
        s = "+" + s

    # Basic sanity check: must be + and 7..15 digits
    digits = re.sub(r"\D", "", s)
    if len(digits) < 7 or len(digits) > 15:
        return ""

    return "+" + digits








