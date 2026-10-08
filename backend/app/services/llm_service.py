"""Gemini LLM service — Product Description Generator (WF004).

Key design decisions
--------------------
* Always loads backend/.env using an absolute path derived from __file__ so
  this module works regardless of the working directory uvicorn is started from.
* Explicitly reads GEMINI_API_KEY (never relies on GOOGLE_API_KEY or ambient
  environment variables to avoid shadowing by stale system-level keys).
* Differentiates exception types so callers receive actionable error messages.
"""
from __future__ import annotations

import os
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# ── Resolve the .env file relative to this file, not the CWD ────────────────
#   __file__  → backend/app/services/llm_service.py
#   parent[0] → backend/app/services/
#   parent[1] → backend/app/
#   parent[2] → backend/              ← .env lives here
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_DOTENV_PATH = _BACKEND_DIR / ".env"

load_dotenv(dotenv_path=_DOTENV_PATH, override=False)   # override=False: .env wins over system env

logger = logging.getLogger(__name__)

# ── Diagnostic boot log (key existence only — value never printed) ───────────
_gemini_key = os.getenv("GEMINI_API_KEY")
_google_key  = os.getenv("GOOGLE_API_KEY")
logger.info("Gemini key loaded: %s  (length %d)", bool(_gemini_key), len(_gemini_key) if _gemini_key else 0)
logger.info("GOOGLE_API_KEY present: %s", bool(_google_key))
logger.info("Loaded .env from: %s", _DOTENV_PATH)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_client() -> genai.Client:
    """Return an initialised Gemini client using GEMINI_API_KEY from the .env."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Gemini API key is missing. "
            f"Add GEMINI_API_KEY=<your-key> to {_DOTENV_PATH}"
        )

    # Explicitly pass api_key so GOOGLE_API_KEY in the environment cannot shadow it.
    return genai.Client(api_key=api_key)


def _classify_gemini_error(exc: Exception) -> str:
    """Map a Gemini SDK exception to a human-readable error message."""
    msg = str(exc).lower()

    # Authentication / permission
    if any(k in msg for k in ("api_key", "api key", "unauthenticated", "permission_denied",
                               "invalid_api_key", "authentication", "forbidden", "401", "403")):
        return (
            "Gemini API authentication failed. "
            "Verify the API key at console.cloud.google.com and that Gemini API is enabled."
        )

    # Quota / rate limit
    if any(k in msg for k in ("quota", "rate_limit", "resource_exhausted", "429")):
        return "Gemini API rate limit reached. Please wait a moment and try again."

    # Model not found
    if any(k in msg for k in ("model_not_found", "not found", "does not exist", "404")):
        return (
            f"Gemini model not found. "
            f"Check GEMINI_MODEL in .env (currently: {os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')})."
        )

    # Network / connection
    if any(k in msg for k in ("connection", "timeout", "network", "unreachable", "resolve")):
        return "Unable to connect to Gemini API. Check your internet connection."

    # Generic fallback — include the original message for diagnostics
    return f"Gemini API error: {exc}"


# ── Public API ────────────────────────────────────────────────────────────────

def generate_product_description(
    product_name: str,
    category: str | None = None,
    attributes: str | None = None,
    material: str | None = None,
    color: str | None = None,
    target_audience: str | None = None,
) -> dict:
    """Generate SEO product content using Gemini API.

    Returns a dict with keys:
        product_description, short_description, seo_title, meta_description,
        missing_attributes, provided_attributes
    Raises RuntimeError with a specific message on any Gemini failure.
    """
    client = _get_client()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # ── Build attribute context ──────────────────────────────────────────────
    provided: dict[str, str] = {}
    missing: list[str] = []

    for field, val in [
        ("product_name",   product_name),
        ("category",       category),
        ("attributes",     attributes),
        ("material",       material),
        ("color",          color),
        ("target_audience", target_audience),
    ]:
        if val and val.strip():
            provided[field] = val.strip()
        elif field != "product_name":   # product_name is always required
            missing.append(field)

    attributes_text = "\n".join(
        f"{k}: {v}" for k, v in provided.items()
    ) + "\n" + "\n".join(
        f"{m}: [NOT PROVIDED]" for m in missing
    )

    prompt = (
        "You are a professional e-commerce copywriter. "
        "Generate product content ONLY based on the provided attributes. "
        "If an attribute is marked as [NOT PROVIDED], do NOT invent it — "
        "write '[Not Provided]' for that field. "
        "Return a JSON object with keys: "
        "product_description, short_description, seo_title, meta_description.\n\n"
        f"Product attributes:\n{attributes_text}"
    )

    # ── Call Gemini ──────────────────────────────────────────────────────────
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )

        if not response or not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        result = json.loads(response.text)
        result["missing_attributes"] = missing
        result["provided_attributes"] = provided
        logger.info("WF004 LLM step succeeded (model=%s).", model)
        return result

    except RuntimeError:
        raise   # already formatted above
    except Exception as exc:
        logger.error("Gemini API error in generate_product_description: %s", exc)
        raise RuntimeError(_classify_gemini_error(exc)) from exc
