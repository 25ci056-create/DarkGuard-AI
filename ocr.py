"""OCR wrapper – EasyOCR first, Tesseract fallback."""
import re
import logging

logger = logging.getLogger(__name__)

# Try EasyOCR
_easyocr_reader = None
_EASYOCR_AVAILABLE = False
try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    pass

# Try Tesseract
_TESSERACT_AVAILABLE = False
try:
    import pytesseract
    pytesseract.get_tesseract_version()
    _TESSERACT_AVAILABLE = True
except Exception:
    pass


def _get_easyocr():
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _easyocr_reader


def _ocr_easyocr(pil_img) -> list[dict]:
    """Return list of {text, bbox, conf}."""
    import numpy as np
    reader = _get_easyocr()
    results = reader.readtext(np.array(pil_img))
    out = []
    for (bbox, text, conf) in results:
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        out.append({
            "text": text,
            "bbox": [min(x_coords), min(y_coords), max(x_coords), max(y_coords)],
            "conf": float(conf),
        })
    return out


def _ocr_tesseract(pil_img) -> list[dict]:
    """Return list of {text, bbox, conf} using Tesseract."""
    import pytesseract
    data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT, lang="eng")
    out = []
    for i, text in enumerate(data["text"]):
        text = (text or "").strip()
        if not text:
            continue
        conf = float(data["conf"][i])
        if conf < 20:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        out.append({"text": text, "bbox": [x, y, x + w, y + h], "conf": conf / 100})
    return out


def extract_text(pil_img) -> list[dict]:
    """Extract text from one image. Returns [{text, bbox, conf}]."""
    if pil_img is None:
        return []
    if _EASYOCR_AVAILABLE:
        try:
            return _ocr_easyocr(pil_img)
        except Exception as exc:
            logger.warning("EasyOCR failed: %s", exc)
    if _TESSERACT_AVAILABLE:
        try:
            return _ocr_tesseract(pil_img)
        except Exception as exc:
            logger.warning("Tesseract failed: %s", exc)
    logger.warning("No OCR engine available – will rely on AI vision only.")
    return []


def extract_text_all(images: dict) -> dict:
    """Run OCR on all slots. Returns {slot: {items: [...], full_text: str}}."""
    results = {}
    for slot, img_data in images.items():
        items = extract_text(img_data.get("pil_img"))
        full_text = " ".join(i["text"] for i in items)
        results[slot] = {"items": items, "full_text": full_text}
    return results


# ── Parsing helpers ───────────────────────────────────────────────────────────

_PRICE_RE = re.compile(r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
_TIMER_RE = re.compile(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b")
_STOCK_RE = re.compile(r"only\s+(\d+)\s+left", re.IGNORECASE)
_DEAL_END_RE = re.compile(r"(deal ends|limited time|offer ends|ends in|hurry)", re.IGNORECASE)


def parse_prices(text: str) -> list[float]:
    return [float(m.replace(",", "")) for m in _PRICE_RE.findall(text)]


def parse_timers(text: str) -> list[str]:
    return [m.group(0) for m in _TIMER_RE.finditer(text)]


def parse_stock_messages(text: str) -> list[str]:
    return _STOCK_RE.findall(text)


def parse_urgency_keywords(text: str) -> list[str]:
    return _DEAL_END_RE.findall(text)
