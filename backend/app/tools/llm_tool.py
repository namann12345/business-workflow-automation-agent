"""LLM tool — Gemini integration for text generation and classification tasks.

Migrated from OpenAI to google-genai.  All workflows that previously used
OpenAI (WF007 Campaign Brief, WF008 SEO Keywords, WF009 Task Assignment) now
call Gemini through this module.

.env is loaded from the backend/ directory using an absolute path so this
module works regardless of which directory uvicorn is launched from.
"""
from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai

# ── Load .env from backend/ via absolute path ────────────────────────────────
#   __file__ → backend/app/tools/llm_tool.py  (parents[2] = backend/)
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_DOTENV_PATH = _BACKEND_DIR / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH, override=False)

logger = logging.getLogger(__name__)
_client: genai.Client | None = None


# ── Internal helpers ─────────────────────────────────────────────────────────

def _get_client() -> genai.Client:
    """Return a cached Gemini client, creating it on first call."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Gemini API key is missing. "
                f"Add GEMINI_API_KEY=<your-key> to {_DOTENV_PATH}"
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _get_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _classify_gemini_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if any(k in msg for k in ("api_key", "api key", "unauthenticated", "permission_denied",
                               "invalid_api_key", "authentication", "forbidden", "401", "403")):
        return (
            "Gemini API authentication failed. "
            "Verify the API key at console.cloud.google.com and that Gemini API is enabled."
        )
    if any(k in msg for k in ("quota", "rate_limit", "resource_exhausted", "429")):
        return "Gemini API rate limit reached. Please wait a moment and try again."
    if any(k in msg for k in ("model_not_found", "not found", "does not exist", "404")):
        return f"Gemini model not found. Check GEMINI_MODEL in .env (current: {_get_model()})."
    if any(k in msg for k in ("connection", "timeout", "network", "unreachable", "resolve")):
        return "Unable to connect to Gemini API. Check your internet connection."
    return f"Gemini API error: {exc}"


# ── Public helpers ────────────────────────────────────────────────────────────

def call_llm(system_prompt: str, user_message: str,
             max_tokens: int = 1500, temperature: float = 0.3) -> str:
    """Call Gemini and return plain text response."""
    client = _get_client()
    combined = f"{system_prompt}\n\n{user_message}"
    try:
        response = client.models.generate_content(
            model=_get_model(),
            contents=combined,
        )
        return (response.text or "").strip()
    except Exception as exc:
        logger.error("Gemini call_llm error: %s", exc)
        raise RuntimeError(_classify_gemini_error(exc)) from exc


def call_llm_json(system_prompt: str, user_message: str, max_tokens: int = 1000) -> Any:
    """Call Gemini expecting a JSON response."""
    client = _get_client()
    combined = f"{system_prompt}\nRespond ONLY with valid JSON.\n\n{user_message}"
    try:
        response = client.models.generate_content(
            model=_get_model(),
            contents=combined,
            config={"response_mime_type": "application/json"},
        )
        text = (response.text or "{}").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as jexc:
            logger.error("Gemini returned invalid JSON: %s", text[:300])
            raise ValueError(f"Gemini returned invalid JSON: {jexc}") from jexc
    except (RuntimeError, ValueError):
        raise
    except Exception as exc:
        logger.error("Gemini call_llm_json error: %s", exc)
        raise RuntimeError(_classify_gemini_error(exc)) from exc


# ── Business logic functions (unchanged signatures) ──────────────────────────

def generate_product_description(
    product_name: str,
    category: str | None = None,
    attributes: str | None = None,
    material: str | None = None,
    color: str | None = None,
    target_audience: str | None = None,
) -> dict:
    """Generate SEO product content (Gemini). Never invents missing attributes."""
    provided: dict[str, str] = {}
    missing: list[str] = []
    for field, val in [
        ("product_name",    product_name),
        ("category",        category),
        ("attributes",      attributes),
        ("material",        material),
        ("color",           color),
        ("target_audience", target_audience),
    ]:
        if val and val.strip():
            provided[field] = val.strip()
        elif field != "product_name":
            missing.append(field)

    system_prompt = (
        "You are a professional e-commerce copywriter. "
        "Generate product content ONLY based on the provided attributes. "
        "If an attribute is marked as [NOT PROVIDED], do NOT invent it — write '[Not Provided]' for that field. "
        "Return a JSON object with keys: product_description, short_description, seo_title, meta_description."
    )
    attributes_text = "\n".join(f"{k}: {v}" for k, v in provided.items()) + "\n" + \
                      "\n".join(f"{m}: [NOT PROVIDED]" for m in missing)

    result = call_llm_json(system_prompt, f"Product attributes:\n{attributes_text}", max_tokens=800)
    result["missing_attributes"] = missing
    result["provided_attributes"] = provided
    return result


def classify_keywords(keywords: list[str]) -> list[dict]:
    """Classify each keyword by search intent using Gemini."""
    system_prompt = (
        "You are an SEO expert. Classify each keyword by search intent. "
        "Categories: informational, commercial, transactional, navigational. "
        "For each keyword return: keyword, intent (the category), priority (high/medium/low), "
        "recommended_target_page (a relevant page type like /blog/, /product/, /category/, /home/). "
        "Return a JSON object with key 'classifications' containing a list."
    )
    keywords_text = "\n".join(f"- {k}" for k in keywords)
    result = call_llm_json(system_prompt, f"Classify these keywords:\n{keywords_text}", max_tokens=1200)
    return result.get("classifications", [])


def generate_campaign_brief(
    campaign_goal: str,
    product_list: str,
    target_audience: str,
    promotion: str,
    campaign_dates: str = "Not specified",
) -> dict:
    """Generate a structured marketing campaign brief using Gemini."""
    system_prompt = (
        "You are a senior marketing strategist. Generate a structured campaign brief. "
        "Return a JSON object with keys: campaign_objective, target_audience_summary, "
        "key_messages, recommended_channels, timeline_summary, campaign_checklist (list of strings), "
        "kpis (list of strings)."
    )
    user_msg = (
        f"Campaign Goal: {campaign_goal}\n"
        f"Products/Collection: {product_list}\n"
        f"Target Audience: {target_audience}\n"
        f"Promotion/Offer: {promotion}\n"
        f"Campaign Dates: {campaign_dates}"
    )
    return call_llm_json(system_prompt, user_msg, max_tokens=1000)


def extract_task_skills(task_description: str) -> list[str]:
    """Use Gemini to extract required skills from a task description."""
    system_prompt = (
        "You are a technical project manager. Extract required skills from the task description. "
        "Return a JSON object with key 'skills' containing a list of skill strings (e.g. ['Python', 'React'])."
    )
    result = call_llm_json(system_prompt, task_description, max_tokens=300)
    return result.get("skills", [])


def generate_assignment_summary(task_description: str, employee: dict, reason: str) -> str:
    """Generate a human-readable task assignment summary using Gemini."""
    system_prompt = "You are a project manager. Write a concise task assignment summary in 2-3 sentences."
    user_msg = (
        f"Task: {task_description}\n"
        f"Assigned to: {employee.get('name')}\n"
        f"Reason: {reason}"
    )
    return call_llm(system_prompt, user_msg, max_tokens=200)
