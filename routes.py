"""Authentication routes – email, Google, Apple."""
import uuid
import secrets
import re
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
from flask import Blueprint, request, jsonify, redirect, session as flask_session

from backend.db import get_db
from backend.config import config
from backend.auth.session import create_session, destroy_session, get_current_user

auth_bp = Blueprint("auth", __name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Simple in-memory rate limiter (per IP, resets on restart)
_rate_store: dict[str, list] = {}

def _rate_limit(ip: str, limit: int = 10, window: int = 60) -> bool:
    """Return True if the IP is over the limit."""
    now = datetime.now(timezone.utc).timestamp()
    timestamps = [t for t in _rate_store.get(ip, []) if now - t < window]
    timestamps.append(now)
    _rate_store[ip] = timestamps
    return len(timestamps) > limit


def _err(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


def _ok(data: dict = None):
    return jsonify({"ok": True, **(data or {})})


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return _err("Unauthorized", 401)
        return f(*args, user=user, **kwargs)
    return decorated


# ── Email / Password ──────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    ip = request.remote_addr or "unknown"
    if _rate_limit(ip, limit=10, window=60):
        return _err("Too many requests. Please wait a minute.", 429)

    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    confirm = data.get("confirm_password") or ""

    if not full_name:
        return _err("Full name is required.")
    if not _EMAIL_RE.match(email):
        return _err("Please enter a valid email address.")
    if len(password) < 8:
        return _err("Password must be at least 8 characters.")
    if password != confirm:
        return _err("Passwords do not match.")

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        return _err("An account with this email already exists.")

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO users (id, full_name, email, password_hash, provider) VALUES (?,?,?,?,?)",
        (user_id, full_name, email, pw_hash, "email"),
    )
    db.commit()

    create_session(user_id, remember=False)
    return _ok({"user": {"id": user_id, "email": email, "full_name": full_name}})


@auth_bp.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr or "unknown"
    if _rate_limit(ip, limit=10, window=60):
        return _err("Too many requests. Please wait a minute.", 429)

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    remember = bool(data.get("remember_me", False))

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    # Generic message – don't reveal whether email exists
    generic = "Incorrect email or password."
    if not row or not row["password_hash"]:
        return _err(generic)
    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return _err(generic)

    create_session(row["id"], remember=remember)
    return _ok({"user": {"id": row["id"], "email": row["email"], "full_name": row["full_name"]}})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    destroy_session()
    return _ok()


@auth_bp.route("/me", methods=["GET"])
def me():
    user = get_current_user()
    if not user:
        return _err("Not authenticated", 401)
    return _ok({"user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "provider": user["provider"]}})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not _EMAIL_RE.match(email):
        return _err("Please enter a valid email address.")

    db = get_db()
    row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if row:
        token = secrets.token_urlsafe(48)
        expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        db.execute(
            "INSERT INTO password_resets (token, user_id, expires_at) VALUES (?,?,?)",
            (token, row["id"], expires),
        )
        db.commit()
        # In production: send email. For now, log the reset link.
        import logging
        logging.getLogger(__name__).info("Password reset token for %s: %s", email, token)

    # Always return the same message to avoid user enumeration
    return _ok({
        "message": "If an account with that email exists, a reset link will be sent. "
                   "No email service is configured — check the server log for the reset token."
    })


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get("token") or ""
    new_password = data.get("password") or ""

    if len(new_password) < 8:
        return _err("Password must be at least 8 characters.")

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    row = db.execute(
        "SELECT * FROM password_resets WHERE token=? AND used=0 AND expires_at > ?",
        (token, now),
    ).fetchone()
    if not row:
        return _err("Reset link is invalid or expired.")

    pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, row["user_id"]))
    db.execute("UPDATE password_resets SET used=1 WHERE token=?", (token,))
    db.commit()
    return _ok({"message": "Password updated. You can now sign in."})


# ── Google OAuth 2.0 ──────────────────────────────────────────────────────────

@auth_bp.route("/google/callback", methods=["POST"])
def google_callback():
    if not config.google_configured:
        return _err("Google sign-in is not configured on this server.", 503)

    data = request.get_json(silent=True) or {}
    credential = data.get("credential") or ""
    if not credential:
        return _err("Missing Google credential.")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as g_requests
        id_info = id_token.verify_oauth2_token(
            credential,
            g_requests.Request(),
            config.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        return _err(f"Google verification failed: {exc}")

    if not id_info.get("email_verified"):
        return _err("Your Google account email is not verified.")

    email = id_info["email"].lower()
    provider_uid = id_info["sub"]
    full_name = id_info.get("name") or email.split("@")[0]

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE provider='google' AND provider_user_id=?", (provider_uid,)).fetchone()
    if not row:
        # Try to link existing email account
        row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if row:
            db.execute("UPDATE users SET provider='google', provider_user_id=? WHERE id=?", (provider_uid, row["id"]))
            db.commit()
        else:
            user_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO users (id, full_name, email, provider, provider_user_id) VALUES (?,?,?,?,?)",
                (user_id, full_name, email, "google", provider_uid),
            )
            db.commit()
            row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    create_session(row["id"])
    return _ok({"user": {"id": row["id"], "email": row["email"], "full_name": row["full_name"]}})


# ── Apple Sign In ─────────────────────────────────────────────────────────────

@auth_bp.route("/apple/callback", methods=["POST"])
def apple_callback():
    if not config.apple_configured:
        return _err("Apple sign-in is not configured on this server.", 503)

    data = request.get_json(silent=True) or {}
    identity_token = data.get("identity_token") or ""
    full_name_data = data.get("full_name") or {}

    if not identity_token:
        return _err("Missing Apple identity token.")

    try:
        import jwt as pyjwt
        import requests as req

        # Fetch Apple's public keys
        jwks = req.get("https://appleid.apple.com/auth/keys", timeout=5).json()
        header = pyjwt.get_unverified_header(identity_token)
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            return _err("Apple key not found.")

        from jwt.algorithms import RSAAlgorithm
        public_key = RSAAlgorithm.from_jwk(key)
        claims = pyjwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=config.APPLE_CLIENT_ID,
            issuer="https://appleid.apple.com",
        )
    except Exception as exc:
        return _err(f"Apple verification failed: {exc}")

    email = (claims.get("email") or "").lower()
    provider_uid = claims["sub"]

    # Apple sends name only on first auth
    given = (full_name_data.get("givenName") or "").strip()
    family = (full_name_data.get("familyName") or "").strip()
    full_name = f"{given} {family}".strip() or email.split("@")[0]

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE provider='apple' AND provider_user_id=?", (provider_uid,)).fetchone()
    if not row:
        row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if row:
            db.execute("UPDATE users SET provider='apple', provider_user_id=? WHERE id=?", (provider_uid, row["id"]))
            db.commit()
        else:
            user_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO users (id, full_name, email, provider, provider_user_id) VALUES (?,?,?,?,?)",
                (user_id, full_name, email, "apple", provider_uid),
            )
            db.commit()
            row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    create_session(row["id"])
    return _ok({"user": {"id": row["id"], "email": row["email"], "full_name": row["full_name"]}})
