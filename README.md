# DarkGuard AI

**Spot hidden fees, fake urgency timers, and sneaky add-ons in Indian checkout flows.**

> Built for hackathons. Analyses screenshots using OCR, price logic, and Gemini Vision AI. Returns a Trust Score, five CCPA dark-pattern checks with evidence, and a downloadable complaint summary.

---

## Quick Start (Windows / PowerShell)

```powershell
# 1. Enter project folder
cd darkguard-ai

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment variables
Copy-Item .env.example .env
# Then open .env in a text editor and fill in at least SECRET_KEY

# 5. Run
python -m backend.app
```

Open **http://127.0.0.1:5000** in your browser.

---

## Environment Variables (`.env`)

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | **Yes** | Random string for Flask sessions. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_PATH` | No | SQLite file path (default: `darkguard.db`) |
| `GEMINI_API_KEY` | Recommended | Get from [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GEMINI_MODEL` | No | Default: `gemini-1.5-flash` |
| `GOOGLE_CLIENT_ID` | Optional | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Optional | Google OAuth client secret |
| `APPLE_CLIENT_ID` | Optional | Apple Services ID |
| `APPLE_TEAM_ID` | Optional | Apple developer Team ID |
| `APPLE_KEY_ID` | Optional | Apple key ID |
| `APPLE_PRIVATE_KEY` | Optional | Apple private key (PEM string) |

---

## Architecture

```
darkguard-ai/
├── backend/
│   ├── app.py          # Flask factory, routes, serves /frontend
│   ├── config.py       # Loads .env
│   ├── db.py           # SQLite + schema
│   ├── auth/           # Email auth, Google, Apple, sessions
│   ├── audits/         # Upload handling, audit jobs, status polling
│   ├── analysis/
│   │   ├── preprocess.py   # OpenCV: orient, resize, denoise
│   │   ├── ocr.py          # EasyOCR / Tesseract wrapper + parsers
│   │   ├── pricing.py      # Price trail + drip-fee detection
│   │   ├── llm.py          # Gemini vision + simulated fallback
│   │   ├── rules.py        # CCPA 2023 rule-mapping table
│   │   └── scoring.py      # Deterministic trust score (0–10)
│   └── reports/        # PDF (reportlab) + TXT complaint generator
├── frontend/
│   ├── login.html      # Auth page (lavender theme)
│   ├── app.html        # App shell (cream + deep green)
│   ├── css/            # base.css, theme-auth.css, theme-app.css
│   └── js/             # api.js, auth.js, app.js, store.js, upload.js, report.js
└── tests/
    ├── test_backend.py      # pytest test suite
    └── generate_samples.py  # Creates sample checkout screenshots
```

### How analysis works

1. **Preprocess** (OpenCV + Pillow): orient, resize to max 1600 px, denoise, convert to base64 for the AI.
2. **OCR** (EasyOCR first, Tesseract fallback): extract text with bounding boxes. Parse prices (`₹`, `Rs`, `INR`), timers, stock messages, urgency keywords.
3. **Price logic** (Python): compare product → cart → payment totals. Flag every new fee that appears only at checkout (drip pricing).
4. **Vision AI** (Gemini): send three images + OCR text + price facts. Require strict JSON (pydantic-validated). Retry once on bad output. Cross-check AI claims against OCR facts.
5. **Trust Score** (deterministic): start at 10, subtract weighted penalties per FOUND/WARNING × confidence. Clamp 0–10.
6. **Persist** (SQLite): audit id, platform, timestamps, full results JSON.

### Simulated mode

If `GEMINI_API_KEY` is missing or the API fails, the system falls back to rule-based analysis using OCR and price facts only. The report card, PDF, and shared text all display **"SIMULATED DEMO RESULTS: AI not configured"**. No hardcoded results are ever presented as real AI output.

---

## Setting Up Google OAuth

1. Go to [Google Cloud Console → APIs & Credentials](https://console.cloud.google.com/apis/credentials).
2. Create an **OAuth 2.0 Client ID** (Web application).
3. Add Authorised JavaScript origins: `http://localhost:5000`
4. Add Authorised redirect URIs: `http://localhost:5000/api/auth/google/callback`
5. Copy **Client ID** and **Client secret** into `.env`.

## Setting Up Apple Sign In

> **Requires a paid Apple Developer account and an HTTPS domain in production.**

1. Go to [Apple Developer → Certificates, Identifiers & Profiles](https://developer.apple.com/account/resources/identifiers/list/serviceId).
2. Create a **Services ID** (your `APPLE_CLIENT_ID`).
3. Enable **Sign In with Apple**, configure the return URL: `http://localhost:5000/api/auth/apple/callback` (HTTPS required in production).
4. Create a **Sign In with Apple** private key; download the `.p8` file.
5. Set `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` (paste the PEM contents, replacing newlines with `\n`) in `.env`.

---

## Running Tests

```powershell
# From project root with venv active
pip install pytest
pytest tests/ -v
```

## Generating Sample Screenshots

```powershell
python tests/generate_samples.py
```

Creates `tests/sample_screenshots/` with three Flipkart-style images:
- `1_product_page.jpg` – shows ₹499 with urgency timer and "Only 3 left!"
- `2_cart_page.jpg` – shows ₹499 with a pre-ticked "Complete Mobile Protection" add-on
- `3_payment_page.jpg` – reveals a ₹49 platform fee (drip pricing) for the first time

---

## Installing Tesseract (Optional)

Tesseract is used as a fallback OCR engine. EasyOCR works out-of-the-box; Tesseract is optional.

1. Download the Windows installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
2. Run the installer; note the install path (e.g. `C:\Program Files\Tesseract-OCR`).
3. Add Tesseract to your PATH, **or** set it in Python before importing:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

---

## CCPA References

> **Important:** The rule references in `backend/analysis/rules.py` map to the CCPA Dark Patterns Guidelines, 2023, as published by the Central Consumer Protection Authority. Verify the exact clause numbers and annexure items against the [official guideline text](https://consumeraffairs.nic.in/) before using in a formal complaint.

---

## Security Notes

- Secrets are loaded only from `.env` and never exposed to the browser.
- Passwords are hashed with **bcrypt**.
- Sessions use `httpOnly`, `SameSite=Lax` cookies.
- File uploads are validated by magic bytes (not just extension), capped at 10 MB each.
- Uploaded screenshots are deleted after analysis by default (`DELETE_UPLOADS_AFTER_AUDIT=true`).
- CORS is restricted to `localhost:5000`.

---

## Disclaimer

DarkGuard AI is an automated analysis tool for educational and consumer-awareness purposes. It is not legal advice. For formal complaints, contact the [National Consumer Helpline (1915)](https://consumerhelpline.gov.in) or file through [e-Daakhil](https://edaakhil.nic.in).
