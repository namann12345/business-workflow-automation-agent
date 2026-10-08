"""Analytics tool — execution log analysis for WF010."""
from __future__ import annotations
import logging
import sqlite3
import json
from pathlib import Path
from app.config import DB_PATH, FAILURE_RATE_THRESHOLD, SLOW_EXECUTION_THRESHOLD

logger = logging.getLogger(__name__)


def get_execution_logs(limit: int = 1000) -> list[dict]:
    """Fetch all execution logs from SQLite."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT * FROM execution_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def compute_performance_report(logs: list[dict]) -> dict:
    """
    Compute per-workflow performance metrics from execution logs.
    Returns a dict with workflow-level stats and overall summary.
    """
    from collections import defaultdict
    stats: dict[str, dict] = defaultdict(lambda: {
        "workflow_name": "",
        "total": 0,
        "successes": 0,
        "failures": 0,
        "durations": [],
        "errors": [],
        "flagged": False,
    })

    for log in logs:
        wid = log.get("workflow_id", "UNKNOWN")
        s = stats[wid]
        s["workflow_name"] = log.get("workflow_name", wid)
        s["total"] += 1
        if log.get("status") == "success":
            s["successes"] += 1
        else:
            s["failures"] += 1
            if log.get("error_details"):
                s["errors"].append(log["error_details"])

        dur = log.get("duration_seconds")
        if dur is not None:
            try:
                s["durations"].append(float(dur))
            except (TypeError, ValueError):
                pass

    results = []
    for wid, s in stats.items():
        total = s["total"]
        suc = s["successes"]
        fail = s["failures"]
        fail_rate = (fail / total * 100) if total else 0.0
        avg_dur = (sum(s["durations"]) / len(s["durations"])) if s["durations"] else 0.0
        flagged = fail_rate > FAILURE_RATE_THRESHOLD or avg_dur > SLOW_EXECUTION_THRESHOLD

        top_errors: dict[str, int] = {}
        for e in s["errors"]:
            top_errors[e[:100]] = top_errors.get(e[:100], 0) + 1

        results.append({
            "workflow_id": wid,
            "workflow_name": s["workflow_name"],
            "total_executions": total,
            "successes": suc,
            "failures": fail,
            "success_rate_pct": round((suc / total * 100) if total else 0.0, 2),
            "failure_rate_pct": round(fail_rate, 2),
            "avg_duration_seconds": round(avg_dur, 3),
            "flagged": flagged,
            "flag_reason": (
                ("High failure rate; " if fail_rate > FAILURE_RATE_THRESHOLD else "")
                + ("Slow execution" if avg_dur > SLOW_EXECUTION_THRESHOLD else "")
            ).strip("; ") or None,
            "frequent_errors": dict(sorted(top_errors.items(), key=lambda x: -x[1])[:3]),
        })

    results.sort(key=lambda x: (-x["failures"], -x["avg_duration_seconds"]))
    total_logs = len(logs)
    total_failures = sum(r["failures"] for r in results)
    return {
        "total_executions": total_logs,
        "total_failures": total_failures,
        "overall_success_rate_pct": round(((total_logs - total_failures) / total_logs * 100) if total_logs else 0.0, 2),
        "workflows": results,
        "thresholds": {
            "failure_rate_pct": FAILURE_RATE_THRESHOLD,
            "avg_duration_seconds": SLOW_EXECUTION_THRESHOLD,
        },
    }
