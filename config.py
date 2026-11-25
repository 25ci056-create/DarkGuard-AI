"""DarkGuard AI – configuration loader."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
_root = Path(__file__).parent.parent
load_dotenv(_root / ".env")


def _bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes")


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "darkguard.db")

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Apple
    APPLE_CLIENT_ID: str = os.getenv("APPLE_CLIENT_ID", "")
    APPLE_TEAM_ID: str = os.getenv("APPLE_TEAM_ID", "")
    APPLE_KEY_ID: str = os.getenv("APPLE_KEY_ID", "")
    APPLE_PRIVATE_KEY: str = os.getenv("APPLE_PRIVATE_KEY", "")
    APPLE_REDIRECT_URI: str = os.getenv("APPLE_REDIRECT_URI", "http://localhost:5000/api/auth/apple/callback")

    # Session
    SESSION_LIFETIME_DAYS: int = int(os.getenv("SESSION_LIFETIME_DAYS", "1"))
    REMEMBER_ME_DAYS: int = int(os.getenv("REMEMBER_ME_DAYS", "30"))

    # Upload
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH_MB", "30")) * 1024 * 1024
    DELETE_UPLOADS_AFTER_AUDIT: bool = _bool("DELETE_UPLOADS_AFTER_AUDIT", True)

    @property
    def google_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def apple_configured(self) -> bool:
        return bool(self.APPLE_CLIENT_ID and self.APPLE_TEAM_ID and self.APPLE_KEY_ID and self.APPLE_PRIVATE_KEY)

    @property
    def ai_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)


config = Config()
