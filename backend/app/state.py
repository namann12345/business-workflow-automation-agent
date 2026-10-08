"""App-level state — module variables to share singletons across routes."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agent.agent import WorkflowAgent
    from app.workflow.registry import WorkflowRegistry

# Set during startup in main.py
agent: "WorkflowAgent | None" = None
registry: "WorkflowRegistry | None" = None
