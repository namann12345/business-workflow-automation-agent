"""FastAPI routes — Workflows endpoint."""
from __future__ import annotations
from fastapi import APIRouter
from app import state as app_state

router = APIRouter()


@router.get("")
async def list_workflows():
    """List all available workflows from the registry."""
    registry = app_state.registry
    workflows = registry.list_all()
    return {
        "count": len(workflows),
        "workflows": [
            {
                "workflow_id": wf.workflow_id,
                "workflow_name": wf.workflow_name,
                "trigger": wf.trigger,
                "inputs": wf.inputs_list(),
                "tools": wf.tools_list(),
                "expected_output": wf.expected_output,
            }
            for wf in workflows
        ],
    }


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a single workflow definition by ID."""
    registry = app_state.registry
    wf = registry.get(workflow_id.upper())
    if wf is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return {
        "workflow_id": wf.workflow_id,
        "workflow_name": wf.workflow_name,
        "trigger": wf.trigger,
        "inputs": wf.inputs,
        "steps": wf.steps_list(),
        "decision_logic": wf.decision_logic,
        "tools_required": wf.tools_list(),
        "expected_output": wf.expected_output,
    }
