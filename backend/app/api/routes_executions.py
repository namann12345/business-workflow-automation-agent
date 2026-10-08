"""FastAPI routes — Executions endpoint."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
async def list_executions(limit: int = 100):
    """Return recent execution log entries."""
    from app.services.logging_service import get_all_executions
    return {"executions": get_all_executions(limit=limit)}


@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    """Get a single execution record by ID."""
    from app.services.logging_service import get_execution
    record = get_execution(execution_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")
    return record
