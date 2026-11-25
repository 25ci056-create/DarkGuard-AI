"""Health check endpoint."""
from flask import Blueprint, jsonify
from backend.config import config

health_bp = Blueprint("health", __name__)

try:
    import easyocr
    _ocr_available = "easyocr"
except ImportError:
    _ocr_available = None

try:
    import pytesseract
    if not _ocr_available:
        _ocr_available = "tesseract"
except ImportError:
    pass


@health_bp.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "ai": {"configured": config.ai_configured, "model": config.GEMINI_MODEL if config.ai_configured else None},
        "ocr": {"available": _ocr_available or "none"},
        "google": {"configured": config.google_configured},
        "apple": {"configured": config.apple_configured},
    })
