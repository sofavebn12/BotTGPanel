from flask import Blueprint, render_template, request
from server.utils.referral_logging import log_referral_action

auth_start_bp = Blueprint("auth_start", __name__)


@auth_start_bp.get("/auth_start")
def auth_start():
    # Try to get user_id from query params or initData
    user_id = None
    try:
        # Check query params first
        user_id_param = request.args.get("user_id")
        if user_id_param:
            user_id = int(user_id_param)
        # TODO: Could also parse from initData if available
    except (ValueError, TypeError):
        pass
    
    # Log webapp open if user_id is available
    if user_id:
        log_referral_action(user_id, "webapp_open", None)
    
    return render_template("auth_start.html")





