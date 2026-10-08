"""Pydantic models for workflow definitions and execution results."""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class WorkflowDefinition(BaseModel):
    """Represents one workflow loaded from the Excel file."""
    workflow_id: str
    workflow_name: str
    trigger: str
    inputs: str
    steps: str
    decision_logic: str
    tools_required: str
    expected_output: str

    def steps_list(self) -> list[str]:
        """Parse the steps string into a list of step names."""
        return [s.strip() for s in self.steps.replace("→", "->").split("->") if s.strip()]

    def tools_list(self) -> list[str]:
        """Parse the tools_required string into a list of tool names."""
        return [t.strip().lower() for t in self.tools_required.replace(";", ",").split(",") if t.strip()]

    def inputs_list(self) -> list[str]:
        """Parse the inputs string into a list of input names."""
        return [i.strip() for i in self.inputs.replace(";", ",").split(",") if i.strip()]


class StepResult(BaseModel):
    """Result of a single workflow step."""
    name: str
    status: str  # success | failed | skipped
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class ExecutionResult(BaseModel):
    """Full result of a workflow execution."""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    workflow_name: str
    user_request: str
    status: str  # success | failed | partial
    steps: list[StepResult] = []
    conditions: list[dict] = []
    errors: list[str] = []
    final_result: Optional[Any] = None
    metadata: dict = {}
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_seconds: float = 0.0

    def to_log_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "user_request": self.user_request,
            "timestamp": self.timestamp,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "completed_steps": [s.name for s in self.steps if s.status == "success"],
            "failed_steps": [s.name for s in self.steps if s.status == "failed"],
            "error_details": "; ".join(self.errors) if self.errors else None,
            "result_summary": str(self.final_result)[:500] if self.final_result else None,
        }


class RoutingResult(BaseModel):
    """Result from the AI workflow router."""
    workflow_id: Optional[str] = None
    confidence: float = 0.0
    reason: str = ""
    needs_clarification: bool = False
    clarification_message: Optional[str] = None


class AgentRequest(BaseModel):
    """Incoming request from the frontend."""
    request: str
    context: dict = {}
    file_path: Optional[str] = None  # path to uploaded temp file


class AgentResponse(BaseModel):
    """Response sent back to the frontend."""
    routing: RoutingResult
    execution: Optional[ExecutionResult] = None
    message: str = ""
