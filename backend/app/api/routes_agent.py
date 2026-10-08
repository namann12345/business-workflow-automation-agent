"""FastAPI routes — Agent endpoint."""
from __future__ import annotations
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.workflow.models import AgentRequest, AgentResponse
from app.agent.agent import WorkflowAgent
from app.workflow.registry import WorkflowRegistry

logger = logging.getLogger(__name__)
router = APIRouter()


def get_agent(request) -> WorkflowAgent:
    """Retrieve the WorkflowAgent from app state."""
    return request.app.state.agent


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    request: str = Form(...),
    context: str = Form("{}"),
    file: UploadFile | None = File(None),
):
    """
    Main agent endpoint. Accepts a natural-language request, optional context JSON,
    and an optional file upload. Routes to the appropriate workflow and returns results.
    """
    import json
    from fastapi import Request

    try:
        ctx = json.loads(context) if context else {}
    except json.JSONDecodeError:
        ctx = {}

    if file is not None:
        contents = await file.read()
        ctx["file_content"] = contents
        ctx["file_name"] = file.filename or "upload"

    # Get agent from app state (set in main.py lifespan)
    from app.agent.agent import WorkflowAgent
    from app.workflow.registry import WorkflowRegistry
    # We'll use a module-level agent reference
    from app import state as app_state
    agent: WorkflowAgent = app_state.agent

    agent_req = AgentRequest(request=request, context=ctx)
    try:
        response = agent.run(agent_req)
        # Convert bytes from context before serializing (not serializable)
        if response.execution:
            for step in response.execution.steps:
                if step.output and isinstance(step.output, bytes):
                    step.output = None
        return response
    except ValueError as exc:
        # User-facing validation errors — show the message directly
        logger.warning("Validation error in agent run: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        # Unexpected server errors — log full traceback, return generic message
        logger.exception("Unexpected agent run failure")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request. Please check the server logs for details."
        )
