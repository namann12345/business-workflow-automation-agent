"""Employee tool — employee data access and ranking for task assignment."""
from __future__ import annotations
import logging
import pandas as pd
from app.tools.csv_tool import read_csv
from app.config import DATA_DIR

logger = logging.getLogger(__name__)


def get_employees() -> pd.DataFrame:
    """Load employee data from sample CSV."""
    return read_csv(DATA_DIR / "sample_employees.csv")


def rank_employees_for_task(task_description: str, required_skills: list[str]) -> list[dict]:
    """
    Rank employees for a given task based on skill match and available capacity.
    Returns sorted list (best first).
    """
    df = get_employees()
    required = {"name", "skills", "current_workload", "max_workload"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Employee data missing columns: {missing}")

    results = []
    for _, emp in df.iterrows():
        emp_skills_raw = str(emp.get("skills", ""))
        emp_skills = [s.strip().lower() for s in emp_skills_raw.replace(";", ",").split(",")]
        
        matched = [s for s in required_skills if s.lower() in emp_skills]
        skill_score = len(matched) / max(len(required_skills), 1)

        current_wl = float(emp.get("current_workload", 0))
        max_wl = float(emp.get("max_workload", 10))
        capacity = max(0.0, max_wl - current_wl)
        capacity_score = capacity / max(max_wl, 1)

        # Combined score: 60% skill match, 40% capacity
        combined_score = 0.6 * skill_score + 0.4 * capacity_score

        results.append({
            "name": emp["name"],
            "skills": emp_skills_raw,
            "matched_skills": matched,
            "current_workload": current_wl,
            "max_workload": max_wl,
            "capacity": capacity,
            "skill_score": round(skill_score, 3),
            "capacity_score": round(capacity_score, 3),
            "combined_score": round(combined_score, 3),
            "available": capacity > 0,
        })

    return sorted(results, key=lambda x: -x["combined_score"])
