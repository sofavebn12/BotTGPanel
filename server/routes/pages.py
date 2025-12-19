from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/code")
def code_page():
    return render_template("code.html")


@pages_bp.get("/password")
def password_page():
    return render_template("password.html")


@pages_bp.get("/success")
def success_page():
    return render_template("success.html")


@pages_bp.get("/inventory")
def inventory_page():
    return render_template("inventory.html")








