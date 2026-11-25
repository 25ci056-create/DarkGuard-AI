"""DarkGuard AI – Flask application entry point."""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when run via `python -m backend.app`
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from flask import Flask, send_from_directory, redirect, url_for
from flask_cors import CORS

from backend.config import config
from backend.db import init_db, get_db

# ── Blueprint imports ─────────────────────────────────────────────────────────
from backend.auth.routes import auth_bp
from backend.audits.routes import audits_bp
from backend.audits.health import health_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(_root / "frontend"),
        static_url_path="/static",
    )

    # Config
    app.secret_key = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False  # True in production (HTTPS)

    CORS(app, supports_credentials=True, origins=["http://localhost:5000", "http://127.0.0.1:5000"])

    # Init DB
    with app.app_context():
        init_db()
        # Ensure upload folder exists
        upload_path = _root / config.UPLOAD_FOLDER
        upload_path.mkdir(exist_ok=True)

    # Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(audits_bp, url_prefix="/api/audits")
    app.register_blueprint(health_bp)

    # ── Frontend serving ──────────────────────────────────────────────────────
    @app.route("/")
    def root():
        return redirect("/login")

    @app.route("/login")
    def login_page():
        return send_from_directory(str(_root / "frontend"), "login.html")

    @app.route("/app")
    def app_page():
        """Protected – redirect to login if not authenticated."""
        from backend.auth.session import get_current_user
        user = get_current_user()
        if not user:
            return redirect("/login")
        return send_from_directory(str(_root / "frontend"), "app.html")

    @app.route("/frontend/<path:filename>")
    def frontend_files(filename):
        return send_from_directory(str(_root / "frontend"), filename)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
