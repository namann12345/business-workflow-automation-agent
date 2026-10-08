"""
Standalone Gemini connectivity test.

Run from ANY directory:
    python backend/test_gemini.py
    # — or —
    cd backend && python test_gemini.py

Outputs (never prints the API key):
    GEMINI_KEY_LOADED=True|False
    GEMINI_KEY_LENGTH=<n>
    GOOGLE_API_KEY_PRESENT=True|False
    DOTENV_LOADED_FROM=<path>
    GEMINI_MODEL=<model>
    GEMINI_TEST=SUCCESS|FAILED
    ERROR_TYPE=<exception class>      (only on failure)
    ERROR_DETAIL=<message>            (only on failure)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Load .env from backend/ regardless of CWD ───────────────────────────────
#   This file lives at backend/test_gemini.py → parent = backend/
_BACKEND_DIR = Path(__file__).resolve().parent
_DOTENV_PATH = _BACKEND_DIR / ".env"

from dotenv import load_dotenv
load_dotenv(dotenv_path=_DOTENV_PATH, override=False)

print(f"DOTENV_LOADED_FROM={_DOTENV_PATH}")

# ── Check env vars ────────────────────────────────────────────────────────────
gemini_key  = os.getenv("GEMINI_API_KEY")
google_key  = os.getenv("GOOGLE_API_KEY")

print(f"GEMINI_KEY_LOADED={bool(gemini_key)}")
print(f"GEMINI_KEY_LENGTH={len(gemini_key) if gemini_key else 0}")
print(f"GOOGLE_API_KEY_PRESENT={bool(google_key)}")

if not gemini_key:
    print("GEMINI_TEST=FAILED")
    print("ERROR_TYPE=MissingKeyError")
    print(f"ERROR_DETAIL=GEMINI_API_KEY not found in {_DOTENV_PATH}")
    sys.exit(1)

# ── Attempt Gemini API call ───────────────────────────────────────────────────
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
print(f"GEMINI_MODEL={model}")

try:
    from google import genai
    # Explicitly use GEMINI_API_KEY so GOOGLE_API_KEY cannot shadow it.
    client = genai.Client(api_key=gemini_key)
    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly the text: GEMINI_OK",
    )
    text = (response.text or "").strip()
    print(f"GEMINI_TEST=SUCCESS")
    print(f"GEMINI_RESPONSE={text}")
except Exception as exc:
    print(f"GEMINI_TEST=FAILED")
    print(f"ERROR_TYPE={type(exc).__name__}")
    # Print error detail but NOT the key value
    safe_msg = str(exc).replace(gemini_key, "***REDACTED***") if gemini_key else str(exc)
    print(f"ERROR_DETAIL={safe_msg}")
    sys.exit(1)
