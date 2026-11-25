"""Tests for DarkGuard AI backend."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import io
import pytest
from backend.app import create_app


@pytest.fixture
def app(tmp_path):
    """Create a test Flask app with a temp DB."""
    import os
    os.environ["DATABASE_PATH"] = str(tmp_path / "test.db")
    os.environ["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["DELETE_UPLOADS_AFTER_AUDIT"] = "false"
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# ── Health ────────────────────────────────────────────────────────────────────
def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "ai" in data
    assert "ocr" in data
    assert "google" in data
    assert "apple" in data


# ── Auth: register & login ────────────────────────────────────────────────────
def test_register_and_login(client):
    # Register
    res = client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "securePass1!",
        "confirm_password": "securePass1!",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["user"]["email"] == "test@example.com"

    # Logout
    client.post("/api/auth/logout")

    # Login
    res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "securePass1!",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True

    # Me
    res = client.get("/api/auth/me")
    assert res.get_json()["ok"] is True


def test_wrong_password(client):
    client.post("/api/auth/register", json={
        "full_name": "X",
        "email": "x@test.com",
        "password": "password123",
        "confirm_password": "password123",
    })
    client.post("/api/auth/logout")
    res = client.post("/api/auth/login", json={"email": "x@test.com", "password": "wrong"})
    data = res.get_json()
    assert data["ok"] is False


def test_duplicate_email(client):
    for _ in range(2):
        res = client.post("/api/auth/register", json={
            "full_name": "Dup",
            "email": "dup@test.com",
            "password": "password123",
            "confirm_password": "password123",
        })
    assert res.get_json()["ok"] is False


def test_app_redirect_unauthenticated(client):
    res = client.get("/app", follow_redirects=False)
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


# ── Analysis: pricing ─────────────────────────────────────────────────────────
def test_price_comparison():
    from backend.analysis.pricing import compare_prices
    ocr = {
        1: {"full_text": "₹499 Add to cart Buy now", "items": []},
        2: {"full_text": "₹499 Cart total", "items": []},
        3: {"full_text": "₹499 Platform fee ₹49 Total ₹548", "items": []},
    }
    facts = compare_prices(ocr)
    assert len(facts["new_fees"]) > 0 or facts["price_increase"] >= 0


def test_ocr_price_parser():
    from backend.analysis.ocr import parse_prices
    prices = parse_prices("₹1,299 was ₹2,499 save ₹1,200 Rs. 49 platform fee")
    assert 1299.0 in prices or 2499.0 in prices


# ── Trust score ───────────────────────────────────────────────────────────────
def test_trust_score_full_clear():
    from backend.analysis.scoring import compute_trust_score
    result = {"patterns": [
        {"pattern_key": k, "status": "CLEAR", "confidence": 1.0}
        for k in ["drip_pricing", "false_urgency", "basket_sneaking", "forced_action", "bait_and_switch"]
    ]}
    ts = compute_trust_score(result)
    assert ts["score"] == 10.0
    assert ts["label"] == "Looks safe"


def test_trust_score_all_found():
    from backend.analysis.scoring import compute_trust_score
    result = {"patterns": [
        {"pattern_key": k, "status": "FOUND", "confidence": 1.0}
        for k in ["drip_pricing", "false_urgency", "basket_sneaking", "forced_action", "bait_and_switch"]
    ]}
    ts = compute_trust_score(result)
    assert ts["score"] == 0.0
    assert ts["label"] == "High risk"


# ── Simulated analysis ────────────────────────────────────────────────────────
def test_simulated_analysis():
    from backend.analysis.llm import _simulated_result
    ocr = {
        1: {"full_text": "₹499 only 2 left limited time offer", "items": []},
        2: {"full_text": "₹499 Cart", "items": []},
        3: {"full_text": "₹499 platform fee ₹49 Total ₹548", "items": []},
    }
    price_facts = {
        "drip_evidence": ["₹49.00 'platform fee' appeared only on the payment page."],
        "new_fees": {"platform fee": 49.0},
        "price_increase": 49.0,
        "prices_per_slot": {"1": [499.0], "2": [499.0], "3": [499.0, 49.0, 548.0]},
        "totals": {"1": 499.0, "2": 499.0, "3": 548.0},
    }
    result = _simulated_result("Flipkart", ocr, price_facts)
    patterns = result["patterns"]
    assert len(patterns) == 5
    drip = next(p for p in patterns if p["pattern_key"] == "drip_pricing")
    assert drip["status"] == "FOUND"
    urgency = next(p for p in patterns if p["pattern_key"] == "false_urgency")
    assert urgency["status"] in ("WARNING", "FOUND")
