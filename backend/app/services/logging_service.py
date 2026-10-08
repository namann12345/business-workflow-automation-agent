"""Execution logging service — stores all workflow runs in SQLite."""
from __future__ import annotations
import json
import logging
import sqlite3
from pathlib import Path
from app.workflow.models import ExecutionResult
from app.config import DB_PATH

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS execution_logs (
    execution_id    TEXT PRIMARY KEY,
    workflow_id     TEXT NOT NULL,
    workflow_name   TEXT NOT NULL,
    user_request    TEXT,
    timestamp       TEXT,
    status          TEXT,
    duration_seconds REAL,
    completed_steps TEXT,
    failed_steps    TEXT,
    error_details   TEXT,
    result_summary  TEXT
);
"""


def init_db() -> None:
    """Create the SQLite database and table if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()
    conn.close()
    logger.info("Execution log DB ready: %s", DB_PATH)


def log_execution(result: ExecutionResult) -> None:
    """Persist an execution result to SQLite."""
    d = result.to_log_dict()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        INSERT OR REPLACE INTO execution_logs
        (execution_id, workflow_id, workflow_name, user_request, timestamp, status,
         duration_seconds, completed_steps, failed_steps, error_details, result_summary)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            d["execution_id"], d["workflow_id"], d["workflow_name"], d["user_request"],
            d["timestamp"], d["status"], d["duration_seconds"],
            json.dumps(d["completed_steps"]), json.dumps(d["failed_steps"]),
            d["error_details"], d["result_summary"],
        ),
    )
    conn.commit()
    conn.close()


def get_all_executions(limit: int = 200) -> list[dict]:
    """Fetch recent executions from SQLite."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM execution_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["completed_steps"] = json.loads(d.get("completed_steps") or "[]")
            d["failed_steps"] = json.loads(d.get("failed_steps") or "[]")
        except Exception:
            pass
        result.append(d)
    return result


def get_execution(execution_id: str) -> dict | None:
    """Fetch a single execution record."""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM execution_logs WHERE execution_id = ?", (execution_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    try:
        d["completed_steps"] = json.loads(d.get("completed_steps") or "[]")
        d["failed_steps"] = json.loads(d.get("failed_steps") or "[]")
    except Exception:
        pass
    return d
