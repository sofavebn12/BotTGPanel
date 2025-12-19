import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException


def validate_phone_number_e164(phone_number: str) -> tuple[bool, str]:
    """
    Validates a phone number using libphonenumber.
    Expects phone_number to be in E.164-ish format (preferably starts with '+').
    Returns (ok, message_for_user).
    """
    if not phone_number:
        return False, "Введите номер телефона"

    try:
        parsed = phonenumbers.parse(phone_number, None)
    except NumberParseException:
        return False, "Введите корректный номер телефона"

    if not phonenumbers.is_possible_number(parsed):
        return False, "Номер телефона слишком короткий или слишком длинный"

    if not phonenumbers.is_valid_number(parsed):
        return False, "Введите корректный номер телефона"

    return True, ""








