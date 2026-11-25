"""Price comparison logic across checkout steps."""
from backend.analysis.ocr import parse_prices
import re

_FEE_KEYWORDS = [
    "platform fee", "handling fee", "cod charge", "cash on delivery",
    "delivery charge", "delivery fee", "trust shield", "insurance",
    "donation", "convenience fee", "service fee", "packaging fee",
    "processing fee", "subscription", "prime", "extra charge",
]

_FEE_LINE_RE = re.compile(
    r"(" + "|".join(re.escape(k) for k in _FEE_KEYWORDS) + r")[^\n₹Rs\d]*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


def _extract_fees(text: str) -> dict[str, float]:
    fees = {}
    for m in _FEE_LINE_RE.finditer(text):
        name = m.group(1).strip().lower()
        amount = float(m.group(2).replace(",", ""))
        fees[name] = amount
    return fees


def compare_prices(ocr_results: dict) -> dict:
    """
    Returns a dict with:
      - prices_per_slot: {slot: [prices]}
      - fees_per_slot:   {slot: {fee_name: amount}}
      - new_fees:        fees that appear only at payment (slot 3)
      - price_increase:  difference between slot 1 and slot 3 totals
      - drip_evidence:   list of human-readable strings
    """
    prices_per_slot = {}
    fees_per_slot = {}
    for slot, data in ocr_results.items():
        text = data.get("full_text", "")
        prices_per_slot[slot] = parse_prices(text)
        fees_per_slot[slot] = _extract_fees(text)

    # Compute totals (use max price as the "item price" proxy)
    totals = {}
    for slot, prices in prices_per_slot.items():
        totals[slot] = max(prices) if prices else 0.0

    price_increase = totals.get(3, 0.0) - totals.get(1, 0.0)

    # New fees at payment step
    fees_1 = set(fees_per_slot.get(1, {}).keys()) | set(fees_per_slot.get(2, {}).keys())
    fees_3 = fees_per_slot.get(3, {})
    new_fees = {k: v for k, v in fees_3.items() if k not in fees_1}

    drip_evidence = []
    for name, amount in new_fees.items():
        drip_evidence.append(f"₹{amount:.2f} '{name}' appeared only on the payment page.")
    if price_increase > 0 and not new_fees:
        drip_evidence.append(f"Total price increased by ₹{price_increase:.2f} between product page and payment.")

    return {
        "prices_per_slot": {str(k): v for k, v in prices_per_slot.items()},
        "fees_per_slot": {str(k): v for k, v in fees_per_slot.items()},
        "new_fees": new_fees,
        "price_increase": round(price_increase, 2),
        "totals": {str(k): round(v, 2) for k, v in totals.items()},
        "drip_evidence": drip_evidence,
    }
