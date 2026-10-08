"""Main AI Agent — orchestrates routing and execution."""
from __future__ import annotations
import logging
from app.workflow.models import AgentRequest, AgentResponse, RoutingResult, ExecutionResult
from app.agent.router import WorkflowRouter
from app.workflow.registry import WorkflowRegistry
from app.workflow.executor import WorkflowExecutor
from app.services.logging_service import log_execution

logger = logging.getLogger(__name__)


class WorkflowAgent:
    """
    Central orchestrator: receives user requests, routes to the right workflow,
    executes it, logs the result, and returns a structured response.
    """

    def __init__(self, registry: WorkflowRegistry):
        self.registry = registry
        self.router = WorkflowRouter()
        self.executor = WorkflowExecutor()

    def run(self, request: AgentRequest) -> AgentResponse:
        """Full pipeline: Route → Validate → Execute → Log → Respond."""
        # 1. Route
        routing = self.router.route(
            user_request=request.request,
            workflow_metadata=self.registry.metadata_for_router(),
        )

        if routing.needs_clarification or not routing.workflow_id:
            return AgentResponse(
                routing=routing,
                execution=None,
                message=routing.clarification_message or "Please clarify your request.",
            )

        # 2. Retrieve workflow definition
        wf = self.registry.get(routing.workflow_id)
        if wf is None:
            routing.needs_clarification = True
            routing.clarification_message = f"Workflow '{routing.workflow_id}' not found in registry."
            return AgentResponse(routing=routing, execution=None,
                                 message=routing.clarification_message)

        # 3. Extract context from user request (LLM-assisted)
        extracted_context = self.router.extract_context(
            user_request=request.request,
            workflow_id=wf.workflow_id,
            workflow_name=wf.workflow_name,
            required_inputs=wf.inputs_list(),
            decision_logic=wf.decision_logic,
        )

        # Merge with any explicitly provided context (API-level context takes priority)
        context = {**extracted_context, **request.context}
        if request.file_path:
            context["file_path"] = request.file_path
        if "file_content" in request.context:
            context["file_content"] = request.context["file_content"]

        # 4. Execute
        execution_result = self.executor.execute(wf, request.request, context)

        # 5. Log
        try:
            log_execution(execution_result)
        except Exception as exc:
            logger.warning("Failed to log execution: %s", exc)

        return AgentResponse(
            routing=routing,
            execution=execution_result,
            message=_build_message(execution_result),
        )


def _build_message(result: ExecutionResult) -> str:
    if result.status == "success":
        fr = result.final_result
        if isinstance(fr, dict) and "message" in fr:
            return fr["message"]
        return f"Workflow {result.workflow_id} completed successfully."
    if result.status == "needs_clarification":
        fr = result.final_result or {}
        return fr.get("message", "Additional information is required.")
    if result.status == "escalation":
        fr = result.final_result or {}
        return fr.get("message", "Escalation required.")
    return f"Workflow {result.workflow_id} failed: {'; '.join(result.errors)}"
