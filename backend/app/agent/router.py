"""AI Workflow Router — uses Gemini to semantically match user requests to workflows.

Migrated from OpenAI to google-genai. Falls back to keyword-based routing if
the Gemini call fails.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from app.workflow.models import RoutingResult

# ── Load .env (router may be imported before config) ────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=_BACKEND_DIR / ".env", override=False)

from app.agent.prompts import WORKFLOW_ROUTER_SYSTEM_PROMPT, CONTEXT_EXTRACTION_PROMPT
from app.config import ROUTING_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)


def _gemini_client():
    """Return a google.genai Client using GEMINI_API_KEY."""
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)


def _gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class WorkflowRouter:
    """Routes natural-language requests to the correct workflow using Gemini."""

    def route(self, user_request: str, workflow_metadata: list[dict]) -> RoutingResult:
        """Determine which workflow to run for the given user request."""
        workflow_list = json.dumps(workflow_metadata, indent=2)
        system_prompt = WORKFLOW_ROUTER_SYSTEM_PROMPT.format(workflow_list=workflow_list)
        combined = f"{system_prompt}\n\nUser request: {user_request}"

        try:
            client = _gemini_client()
            response = client.models.generate_content(
                model=_gemini_model(),
                contents=combined,
                config={"response_mime_type": "application/json"},
            )
            raw = (response.text or "{}").strip()
            data = json.loads(raw)
        except Exception as exc:
            logger.error("Gemini routing failed: %s — falling back to keyword routing", exc)
            return self._fallback_route(user_request, workflow_metadata)

        # Safety: only accept workflow IDs that exist in registry
        valid_ids = {w["workflow_id"] for w in workflow_metadata}
        wf_id = data.get("workflow_id")
        if wf_id and wf_id not in valid_ids:
            logger.warning("Gemini returned unknown workflow_id '%s' — rejecting.", wf_id)
            wf_id = None
            data["confidence"] = 0.0

        routing = RoutingResult(
            workflow_id=wf_id,
            confidence=float(data.get("confidence", 0.0)),
            reason=str(data.get("reason", "")),
            needs_clarification=bool(data.get("needs_clarification", False)),
            clarification_message=data.get("clarification_message"),
        )

        # If confidence below threshold, force clarification
        if routing.confidence < ROUTING_CONFIDENCE_THRESHOLD and not routing.needs_clarification:
            routing.needs_clarification = True
            routing.workflow_id = None
            wf_names = ", ".join(w["workflow_name"] for w in workflow_metadata)
            routing.clarification_message = (
                "I couldn't confidently identify a matching workflow for your request. "
                f"Available workflows: {wf_names}. "
                "Could you clarify what you'd like to do?"
            )

        return routing

    def extract_context(self, user_request: str, workflow_id: str,
                        workflow_name: str, required_inputs: list[str],
                        decision_logic: str = "") -> dict:
        """Extract structured context values and determine missing required inputs.

        Strategy:
        1. Try Gemini for rich semantic extraction.
        2. If Gemini fails (rate limit / quota / network), fall back to a
           deterministic regex parser that reads explicit 'Label: value' lines.
        """
        system_prompt = CONTEXT_EXTRACTION_PROMPT.format(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            required_inputs=", ".join(required_inputs),
            decision_logic=decision_logic,
            user_message=user_request,
        )
        combined = f"{system_prompt}\n\nUser message: {user_request}"

        try:
            client = _gemini_client()
            response = client.models.generate_content(
                model=_gemini_model(),
                contents=combined,
                config={"response_mime_type": "application/json"},
            )
            raw = (response.text or "{}").strip()
            result = json.loads(raw)

            # New prompt returns {"context": {...}, "missing_required_inputs": [...]}
            if "context" in result:
                ctx = result["context"]
                if not isinstance(ctx, dict):
                    ctx = {}
                ctx["_missing_required_inputs"] = result.get("missing_required_inputs", [])
                logger.info("WF%s context extracted via Gemini (%d fields)", workflow_id, len(ctx))
                return ctx

            # Fallback if Gemini returns flat ctx
            return result

        except Exception as exc:
            logger.warning("Gemini context extraction failed (%s) — using regex fallback parser.", exc)
            return self._regex_extract_context(user_request, required_inputs)

    # ------------------------------------------------------------------
    # Regex-based labeled-field parser (Gemini-unavailable fallback)
    # ------------------------------------------------------------------
    def _regex_extract_context(self, user_request: str, required_inputs: list[str]) -> dict:
        """Parse 'Label: value' lines from raw user prompt into canonical snake_case keys.

        Handles all of:
          - Multi-line structured input:  "Task Description: Build the API."
          - Case variations:              "task description:", "TASK DESCRIPTION:"
          - Trailing whitespace / dots
        """
        import re

        ctx: dict = {}

        # Split into lines, try to parse each "Label: Value" pair
        # Pattern: one or more words (optionally with spaces), colon, then the value
        line_pattern = re.compile(
            r"^([A-Za-z][A-Za-z0-9 _\-]+?)\s*:\s*(.+)$",
            re.MULTILINE,
        )

        for match in line_pattern.finditer(user_request):
            raw_label = match.group(1).strip()
            value = match.group(2).strip()

            # Canonical key: lowercase, spaces → underscores
            canonical = raw_label.lower().replace(" ", "_")
            ctx[canonical] = value

        logger.info(
            "Regex fallback extracted %d field(s) for workflow %s: %s",
            len(ctx),
            required_inputs,
            list(ctx.keys()),
        )
        return ctx



    def _fallback_route(self, user_request: str, workflow_metadata: list[dict]) -> RoutingResult:
        """Simple keyword-based fallback when Gemini is unavailable."""
        req = user_request.lower()
        keyword_map = {
            "WF001": ["restock", "inventory", "stock", "minimum stock"],
            "WF002": ["price", "vendor price", "price difference", "price validation"],
            "WF003": ["vendor file", "vendor spreadsheet", "invalid rows", "vendor data"],
            "WF004": ["seo content", "product description", "generate description", "generate seo", "seo metadata", "meta description", "seo title", "product copy", "product content", "ecommerce product"],
            "WF005": ["order", "ord-", "order status", "where is my order"],
            "WF006": ["duplicate", "duplicates", "similar products"],
            "WF007": ["campaign", "campaign brief", "marketing campaign"],
            "WF008": ["keyword", "keywords", "classify keywords", "search intent", "keyword intent", "analyze keyword", "classify seo"],
            "WF009": ["assign", "task assignment", "employee", "developer", "best available"],
            "WF010": ["performance", "failing", "failure rate", "workflow report", "execution report"],
        }
        valid_ids = {w["workflow_id"] for w in workflow_metadata}
        best_id = None
        best_score = 0
        scores = {}
        for wf_id, keywords in keyword_map.items():
            if wf_id not in valid_ids:
                continue
            score = sum(1 for k in keywords if k in req)
            if score > 0:
                scores[wf_id] = score
            if score > best_score:
                best_score = score
                best_id = wf_id

        # Conflict resolution for combination product + keyword requests
        if "WF004" in scores and "WF008" in scores:
            best_id = "WF004"
            best_score = scores["WF004"]
            
        if best_id and best_score > 0:
            return RoutingResult(
                workflow_id=best_id,
                confidence=min(0.5 + best_score * 0.1, 0.85),
                reason=f"Gemini unavailable — deterministic fallback used. Matched '{best_id}' via keyword scoring. Note: If multiple workflows matched, '{best_id}' was prioritized.",
            )
        return RoutingResult(
            workflow_id=None,
            confidence=0.0,
            reason="Gemini unavailable — no matching workflow found via keywords.",
            needs_clarification=True,
            clarification_message=(
                "I could not identify a matching business workflow for your request. "
                "Please describe your task more specifically (e.g. 'restock check', "
                "'vendor file processing', 'order status')."
            ),
        )
