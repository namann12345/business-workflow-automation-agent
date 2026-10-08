"""WorkflowLoader — reads the Excel file and produces WorkflowDefinition objects."""
from __future__ import annotations
import logging
from pathlib import Path
import pandas as pd
from app.workflow.models import WorkflowDefinition

logger = logging.getLogger(__name__)


class WorkflowLoader:
    """Loads workflow definitions from the Excel specification file."""

    REQUIRED_COLUMNS = [
        "Workflow_ID", "Workflow_Name", "Trigger", "Inputs",
        "Steps", "Decision_Logic", "Tools_Required", "Expected_Output",
    ]

    def __init__(self, excel_path: str | Path):
        self.excel_path = Path(excel_path)

    def load(self) -> list[WorkflowDefinition]:
        """Read the Excel file and return a list of WorkflowDefinition objects."""
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel workflow file not found: {self.excel_path}")

        try:
            df = pd.read_excel(self.excel_path, sheet_name="Workflows")
        except Exception as exc:
            raise ValueError(f"Failed to read 'Workflows' sheet: {exc}") from exc

        self._validate_columns(df)
        workflows = []
        for _, row in df.iterrows():
            wf = WorkflowDefinition(
                workflow_id=str(row["Workflow_ID"]).strip(),
                workflow_name=str(row["Workflow_Name"]).strip(),
                trigger=str(row["Trigger"]).strip(),
                inputs=str(row["Inputs"]).strip(),
                steps=str(row["Steps"]).strip(),
                decision_logic=str(row["Decision_Logic"]).strip(),
                tools_required=str(row["Tools_Required"]).strip(),
                expected_output=str(row["Expected_Output"]).strip(),
            )
            workflows.append(wf)
            logger.info("Loaded workflow: %s — %s", wf.workflow_id, wf.workflow_name)

        logger.info("Total workflows loaded: %d", len(workflows))
        return workflows

    def load_test_questions(self) -> list[dict]:
        """Load the Test_Questions sheet."""
        try:
            df = pd.read_excel(self.excel_path, sheet_name="Test_Questions")
            return df.to_dict(orient="records")
        except Exception as exc:
            logger.warning("Could not load Test_Questions sheet: %s", exc)
            return []

    def _validate_columns(self, df: pd.DataFrame) -> None:
        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Excel 'Workflows' sheet is missing columns: {missing}")
