from flask import Blueprint, redirect, url_for

index_bp = Blueprint("index", __name__)


@index_bp.get("/")
def index():
    return redirect(url_for("auth_start.auth_start"))








