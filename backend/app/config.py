"""Application configuration — loads from environment variables.

.env is loaded from the backend/ directory using an absolute path derived
from __file__ so it works regardless of the working directory uvicorn is
started from.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Resolve paths ────────────────────────────────────────────────────────────
#   __file__ → backend/app/config.py
#   parents[0] → backend/app/
#   parents[1] → backend/           ← .env lives here
#   parents[2] → project root
BACKEND_DIR = Path(__file__).resolve().parents[1]
BASE_DIR    = BACKEND_DIR.parent          # project root
DATA_DIR    = BASE_DIR / "data"
DB_PATH     = BACKEND_DIR / "execution_log.db"

# Load .env from backend/ — override=False so system env can still win when
# explicitly set, but the .env file is the guaranteed fallback.
load_dotenv(dotenv_path=BACKEND_DIR / ".env", override=False)

# Excel source file
EXCEL_PATH = DATA_DIR / "AI_Agent_Workflow_Assessment.xlsx"

# ── Gemini configuration ─────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL:   str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ── Legacy OpenAI (kept in case any non-WF004 code still references it) ──────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL:   str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── Routing / workflow thresholds ─────────────────────────────────────────────
ROUTING_CONFIDENCE_THRESHOLD: float = float(os.getenv("ROUTING_CONFIDENCE_THRESHOLD", "0.6"))
PRICE_DIFF_THRESHOLD:         float = float(os.getenv("PRICE_DIFF_THRESHOLD",         "10.0"))
FAILURE_RATE_THRESHOLD:       float = float(os.getenv("FAILURE_RATE_THRESHOLD",       "10.0"))
SLOW_EXECUTION_THRESHOLD:     float = float(os.getenv("SLOW_EXECUTION_THRESHOLD",     "5.0"))

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
