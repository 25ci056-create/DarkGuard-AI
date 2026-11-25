"""Trust score computation (deterministic)."""


SEVERITY_WEIGHTS = {
    "FOUND_HIGH": 2.5,
    "FOUND": 2.0,
    "WARNING": 1.0,
}

PATTERN_SEVERITY = {
    "drip_pricing": "FOUND_HIGH",
    "false_urgency": "FOUND_HIGH",
    "basket_sneaking": "FOUND",
    "forced_action": "FOUND",
    "bait_and_switch": "FOUND_HIGH",
}


def compute_trust_score(result: dict) -> dict:
    """
    Returns {score: float, label: str, found_count: int, warning_count: int}.
    score is 0–10, one decimal place.
    """
    patterns = result.get("patterns", [])
    deductions = 0.0
    found_count = 0
    warning_count = 0

    for p in patterns:
        status = p.get("status", "CLEAR").upper()
        key = p.get("pattern_key", "")
        confidence = float(p.get("confidence", 1.0))

        if status == "FOUND":
            severity = PATTERN_SEVERITY.get(key, "FOUND")
            weight = SEVERITY_WEIGHTS[severity]
            deductions += weight * confidence
            found_count += 1
        elif status == "WARNING":
            deductions += SEVERITY_WEIGHTS["WARNING"] * confidence
            warning_count += 1

    score = max(0.0, min(10.0, round(10.0 - deductions, 1)))

    if score >= 8.0:
        label = "Looks safe"
        risk = "low"
    elif score >= 5.0:
        label = "Caution"
        risk = "medium"
    else:
        label = "High risk"
        risk = "high"

    return {
        "score": score,
        "label": label,
        "risk": risk,
        "found_count": found_count,
        "warning_count": warning_count,
    }
