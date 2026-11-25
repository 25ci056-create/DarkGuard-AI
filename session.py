"""Session management helpers."""
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from flask import request, session as flask_session
from backend.db import get_db
from backend.config import config


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(user_id: str, remember: bool = False) -> str:
    token = secrets.token_urlsafe(48)
    days = config.REMEMBER_ME_DAYS if remember else config.SESSION_LIFETIME_DAYS
    expires_at = _now() + timedelta(days=days)
    db = get_db()
    db.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at.isoformat()),
    )
    db.commit()
    flask_session["token"] = token
    flask_session.permanent = remember
    return token


def destroy_session():
    token = flask_session.get("token")
    if token:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE token=?", (token,))
        db.commit()
    flask_session.clear()


def get_current_user() -> dict | None:
    token = flask_session.get("token")
    if not token:
        return None
    db = get_db()
    row = db.execute(
        """
        SELECT u.id, u.full_name, u.email, u.provider, s.expires_at
        FROM sessions s JOIN users u ON u.id = s.user_id
        WHERE s.token = ?
        """,
        (token,),
    ).fetchone()
    if not row:
        return None
    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if _now() > expires_at:
        db.execute("DELETE FROM sessions WHERE token=?", (token,))
        db.commit()
        flask_session.clear()
        return None
    return dict(row)
