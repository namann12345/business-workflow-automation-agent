"""WorkflowRegistry — stores loaded workflows and exposes them to the router and executor."""
from __future__ import annotations
import logging
from app.workflow.models import WorkflowDefinition

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """Centralized registry for all workflow definitions."""

    def __init__(self):
        self._workflows: dict[str, WorkflowDefinition] = {}

    def register(self, workflow: WorkflowDefinition) -> None:
        self._workflows[workflow.workflow_id] = workflow
        logger.debug("Registered workflow: %s", workflow.workflow_id)

    def register_all(self, workflows: list[WorkflowDefinition]) -> None:
        for wf in workflows:
            self.register(wf)

    def get(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._workflows.get(workflow_id)

    def get_or_raise(self, workflow_id: str) -> WorkflowDefinition:
        wf = self.get(workflow_id)
        if wf is None:
            raise KeyError(f"Workflow '{workflow_id}' not found in registry.")
        return wf

    def list_all(self) -> list[WorkflowDefinition]:
        return list(self._workflows.values())

    def list_ids(self) -> list[str]:
        return list(self._workflows.keys())

    def metadata_for_router(self) -> list[dict]:
        """Return a minimal JSON-safe summary for the LLM router prompt."""
        return [
            {
                "workflow_id": wf.workflow_id,
                "workflow_name": wf.workflow_name,
                "trigger": wf.trigger,
                "description": wf.inputs,
            }
            for wf in self._workflows.values()
        ]

    def __len__(self) -> int:
        return len(self._workflows)
