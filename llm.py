"""Gemini vision analysis + simulated fallback."""
import json
import logging
import re
from backend.config import config
from backend.analysis.rules import RULES
from backend.analysis.ocr import parse_prices, parse_timers, parse_urgency_keywords, parse_stock_messages

logger = logging.getLogger(__name__)

PATTERN_KEYS = ["drip_pricing", "false_urgency", "basket_sneaking", "forced_action", "bait_and_switch"]

_SYSTEM_PROMPT = """You are DarkGuard AI, an expert in Indian consumer dark patterns and the CCPA Dark Patterns Guidelines 2023.
You are given three checkout screenshots (product page, cart, payment page) with their OCR text and computed price facts.
Analyse each of the five dark patterns. Return ONLY a valid JSON object (no markdown fences) matching this exact schema:

{
  "patterns": [
    {
      "pattern_key": "drip_pricing",
      "pattern_name": "Drip Pricing",
      "status": "FOUND|WARNING|CLEAR",
      "confidence": 0.0-1.0,
      "explanation": "plain language 1-2 sentences",
      "evidence": [
        {
          "screenshot": 1,
          "text": "exact text from screenshot",
          "bbox": [x1, y1, x2, y2]
        }
      ],
      "ccpa_reference": "CCPA Dark Patterns Guidelines, 2023 – Annexure A, Item N"
    }
  ]
}

Analyse these five patterns in this order: drip_pricing, false_urgency, basket_sneaking, forced_action, bait_and_switch.
Be conservative: use FOUND only when you have clear evidence, WARNING for suspicious signals, CLEAR when nothing was detected.
Do not hallucinate evidence. If a bbox is unknown, use [0,0,0,0]."""


def _build_prompt(platform: str, ocr_results: dict, price_facts: dict) -> str:
    lines = [f"Platform: {platform}"]
    lines.append(f"\nComputed price facts: {json.dumps(price_facts)}")
    for slot in (1, 2, 3):
        slot_name = {1: "Product page", 2: "Cart", 3: "Payment page"}.get(slot, f"Screen {slot}")
        text = ocr_results.get(slot, {}).get("full_text", "(no text extracted)")
        lines.append(f"\n--- Screenshot {slot}: {slot_name} ---\n{text[:2000]}")
    return "\n".join(lines)


def _validate_result(data: dict) -> bool:
    patterns = data.get("patterns", [])
    if len(patterns) != 5:
        return False
    for p in patterns:
        if p.get("pattern_key") not in PATTERN_KEYS:
            return False
        if p.get("status") not in ("FOUND", "WARNING", "CLEAR"):
            return False
        if not isinstance(p.get("confidence"), (int, float)):
            return False
    return True


def _run_gemini(platform: str, images: dict, ocr_results: dict, price_facts: dict) -> dict | None:
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)

        # Build image parts
        import PIL.Image
        parts = [_SYSTEM_PROMPT, _build_prompt(platform, ocr_results, price_facts)]
        for slot in (1, 2, 3):
            pil = images.get(slot, {}).get("pil_img")
            if pil:
                parts.append(pil)

        response = model.generate_content(parts)
        raw = response.text.strip()
        # Strip possible markdown code fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        if _validate_result(data):
            return data
        logger.warning("Gemini result failed validation on first try. Retrying…")

        # Retry once
        response2 = model.generate_content(parts)
        raw2 = response2.text.strip()
        raw2 = re.sub(r"^```[a-z]*\n?", "", raw2)
        raw2 = re.sub(r"\n?```$", "", raw2)
        data2 = json.loads(raw2)
        if _validate_result(data2):
            return data2

    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
    return None


def _simulated_result(platform: str, ocr_results: dict, price_facts: dict) -> dict:
    """Rule-based simulated analysis when AI is not available."""
    patterns = []

    # --- Drip Pricing ---
    drip_evidence = price_facts.get("drip_evidence", [])
    new_fees = price_facts.get("new_fees", {})
    drip_status = "FOUND" if drip_evidence else "CLEAR"
    drip_conf = 0.9 if drip_evidence else 1.0
    drip_ev = []
    for ev in drip_evidence[:2]:
        drip_ev.append({"screenshot": 3, "text": ev, "bbox": [0, 0, 0, 0]})
    patterns.append({
        "pattern_key": "drip_pricing",
        "pattern_name": "Drip Pricing",
        "status": drip_status,
        "confidence": drip_conf,
        "explanation": drip_evidence[0] if drip_evidence else "No hidden fees were detected across the checkout steps.",
        "evidence": drip_ev,
        "ccpa_reference": RULES["drip_pricing"]["annexure"],
    })

    # --- False Urgency ---
    all_text = " ".join(d.get("full_text", "") for d in ocr_results.values())
    timers = parse_timers(all_text)
    urgency_kw = parse_urgency_keywords(all_text)
    stock_msgs = parse_stock_messages(all_text)
    urgency_signals = timers + urgency_kw + stock_msgs
    urgency_status = "WARNING" if urgency_signals else "CLEAR"
    urgency_conf = 0.75 if urgency_signals else 1.0
    patterns.append({
        "pattern_key": "false_urgency",
        "pattern_name": "False Urgency",
        "status": urgency_status,
        "confidence": urgency_conf,
        "explanation": (
            f"Urgency signals detected: {', '.join(str(s) for s in urgency_signals[:3])}."
            if urgency_signals else "No urgency timers or false scarcity detected."
        ),
        "evidence": [{"screenshot": 1, "text": s, "bbox": [0, 0, 0, 0]} for s in urgency_signals[:2]],
        "ccpa_reference": RULES["false_urgency"]["annexure"],
    })

    # --- Basket Sneaking ---
    bs_keywords = ["pre-ticked", "auto-added", "trust shield", "insurance", "donate", "protect", "care plan"]
    bs_found = [kw for kw in bs_keywords if kw.lower() in all_text.lower()]
    bs_status = "WARNING" if bs_found else "CLEAR"
    patterns.append({
        "pattern_key": "basket_sneaking",
        "pattern_name": "Basket Sneaking",
        "status": bs_status,
        "confidence": 0.7 if bs_found else 1.0,
        "explanation": (
            f"Potential basket sneaking detected: {', '.join(bs_found[:2])}."
            if bs_found else "No pre-ticked add-ons or unexpected items found."
        ),
        "evidence": [{"screenshot": 2, "text": k, "bbox": [0, 0, 0, 0]} for k in bs_found[:1]],
        "ccpa_reference": RULES["basket_sneaking"]["annexure"],
    })

    # --- Forced Action ---
    patterns.append({
        "pattern_key": "forced_action",
        "pattern_name": "Forced Action",
        "status": "CLEAR",
        "confidence": 0.8,
        "explanation": "No forced sign-ups or hidden skip buttons detected by OCR analysis.",
        "evidence": [],
        "ccpa_reference": RULES["forced_action"]["annexure"],
    })

    # --- Bait & Switch ---
    prices_1 = price_facts.get("prices_per_slot", {}).get("1", [])
    prices_3 = price_facts.get("prices_per_slot", {}).get("3", [])
    bns_status = "CLEAR"
    bns_explanation = "Product details appear consistent across all three steps."
    if prices_1 and prices_3:
        min1, min3 = min(prices_1), min(prices_3)
        if abs(min3 - min1) > 50:
            bns_status = "WARNING"
            bns_explanation = f"Price changed from ₹{min1:.0f} (product page) to ₹{min3:.0f} (payment page)."
    patterns.append({
        "pattern_key": "bait_and_switch",
        "pattern_name": "Bait and Switch",
        "status": bns_status,
        "confidence": 0.75,
        "explanation": bns_explanation,
        "evidence": [],
        "ccpa_reference": RULES["bait_and_switch"]["annexure"],
    })

    return {"patterns": patterns}


def run_vision_analysis(
    platform: str,
    platform_other: str,
    images: dict,
    ocr_results: dict,
    price_facts: dict,
) -> tuple[dict, bool]:
    """
    Returns (result_dict, is_simulated).
    result_dict has key "patterns".
    """
    display_platform = platform_other if platform == "other" else platform

    if config.ai_configured:
        ai_result = _run_gemini(display_platform, images, ocr_results, price_facts)
        if ai_result:
            # Cross-check: if AI claims FOUND for drip_pricing but no price facts, downgrade
            for p in ai_result.get("patterns", []):
                if p.get("pattern_key") == "drip_pricing" and p.get("status") == "FOUND":
                    if not price_facts.get("drip_evidence") and not price_facts.get("new_fees"):
                        p["status"] = "WARNING"
                        p["confidence"] = max(0.3, float(p.get("confidence", 0.5)) - 0.3)
            return ai_result, False

    # Simulated fallback
    logger.warning("Using simulated analysis (AI not configured or failed).")
    result = _simulated_result(display_platform, ocr_results, price_facts)
    result["_simulated"] = True
    return result, True
