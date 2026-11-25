"""CCPA Dark Patterns Guidelines 2023 – rule mapping table."""

# Maps pattern key → CCPA reference details
RULES: dict[str, dict] = {
    "drip_pricing": {
        "pattern_name": "Drip Pricing",
        "ccpa_guideline": "CCPA Dark Patterns Guidelines, 2023",
        "clause": "Guideline 2(1)(iv) – False Representation / Drip Pricing",
        "annexure": "Annexure A, Item 4: Drip Pricing",
        "description": (
            "Drip pricing is showing a base price initially and revealing mandatory fees "
            "or charges only later in the checkout flow, inflating the final price."
        ),
        "consumer_rights": "Right to be informed about the full cost before committing to a purchase.",
    },
    "false_urgency": {
        "pattern_name": "False Urgency",
        "ccpa_guideline": "CCPA Dark Patterns Guidelines, 2023",
        "clause": "Guideline 2(1)(i) – False Urgency",
        "annexure": "Annexure A, Item 1: False Urgency",
        "description": (
            "Creating a false sense of scarcity or time pressure (e.g., fake countdown timers, "
            "inflated 'only X left' messages) to rush consumers into purchases."
        ),
        "consumer_rights": "Right not to be misled by artificial pressure tactics.",
    },
    "basket_sneaking": {
        "pattern_name": "Basket Sneaking",
        "ccpa_guideline": "CCPA Dark Patterns Guidelines, 2023",
        "clause": "Guideline 2(1)(ii) – Basket Sneaking",
        "annexure": "Annexure A, Item 2: Basket Sneaking",
        "description": (
            "Adding products, services (e.g., insurance, subscriptions, donations) or fees "
            "to the cart without explicit user consent, using pre-ticked checkboxes."
        ),
        "consumer_rights": "Right to consent explicitly to every item in the cart.",
    },
    "forced_action": {
        "pattern_name": "Forced Action",
        "ccpa_guideline": "CCPA Dark Patterns Guidelines, 2023",
        "clause": "Guideline 2(1)(iii) – Forced Action / Interface Interference",
        "annexure": "Annexure A, Item 3: Forced Action",
        "description": (
            "Requiring consumers to perform additional, unnecessary actions or sign up for services "
            "to complete a purchase, or using interface tricks (prominent accept, hidden decline)."
        ),
        "consumer_rights": "Right to a clear, unobstructed path to purchase without coerced actions.",
    },
    "bait_and_switch": {
        "pattern_name": "Bait and Switch",
        "ccpa_guideline": "CCPA Dark Patterns Guidelines, 2023",
        "clause": "Guideline 2(1)(v) – Bait and Switch",
        "annexure": "Annexure A, Item 5: Bait and Switch",
        "description": (
            "Advertising a product at a certain price or with certain attributes but substituting "
            "a different product, variant, seller, or higher price by the payment step."
        ),
        "consumer_rights": "Right to receive exactly what was advertised at the stated price.",
    },
}
