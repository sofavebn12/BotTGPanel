from flask import Flask

from server.config.load_env import load_env
from server.routes.auth import auth_bp
from server.routes.auth_start import auth_start_bp
from server.routes.api_auth import api_auth_bp
from server.routes.index import index_bp
from server.routes.pages import pages_bp


def create_app() -> Flask:
    """
    App factory.

    We keep templates in `web/` because your HTML pages already live there.
    Static files are in `web/static/`.
    """
    load_env()

    app = Flask(
        __name__,
        template_folder="../web",
        static_folder="../web/static",
        static_url_path="/static",
    )

    app.register_blueprint(index_bp)
    app.register_blueprint(auth_start_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_auth_bp)

    return app


