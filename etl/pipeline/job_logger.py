"""Lightweight job audit logging for container ETL actions."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTAINER_DATA_ROOT = PROJECT_ROOT / "data" / "container"
LOG_DATA_DIR = CONTAINER_DATA_ROOT / "logs"
RUN_HISTORY_PATH = LOG_DATA_DIR / "run_history.csv"
EDIT_HISTORY_PATH = LOG_DATA_DIR / "edit_history.csv"
RUN_HISTORY_COLUMNS = [
    "job_id",
    "job_type",
    "status",
    "started_at",
    "finished_at",
    "duration_seconds",
    "message",
    "changes",
]


def _json_dumps(value: object) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _history_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return _json_dumps(value)
    return str(value)


@dataclass
class EtlJob:
    """Context manager that records one user-triggered ETL job."""

    job_type: str
    params: dict[str, object] | None = None
    enabled: bool = True
    job_id: str = field(init=False)
    started_at: datetime = field(init=False)

    def __post_init__(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        suffix = uuid4().hex[:8].upper()
        self.job_id = f"JOB-{timestamp}-{suffix}"

    def __enter__(self) -> "EtlJob":
        self.started_at = datetime.now().replace(microsecond=0)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        finished_at = datetime.now().replace(microsecond=0)
        status = "success" if exc_type is None else "failed"
        params = self.params or {}
        self._append_history(
            {
                "job_id": self.job_id,
                "job_type": self.job_type,
                "status": status,
                "started_at": self.started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "duration_seconds": int((finished_at - self.started_at).total_seconds()),
                "message": _history_value(params.get("message", params.get("change_messages"))),
                "changes": _history_value(params.get("changes")),
            }
        )
        return False

    def _append_history(self, row: dict[str, object]) -> None:
        if not self.enabled:
            return

        LOG_DATA_DIR.mkdir(parents=True, exist_ok=True)
        write_header = not RUN_HISTORY_PATH.exists()
        with RUN_HISTORY_PATH.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RUN_HISTORY_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow({column: row.get(column, "") for column in RUN_HISTORY_COLUMNS})

        write_header = not EDIT_HISTORY_PATH.exists()
        if self.job_type == "user_editor_update":
            with EDIT_HISTORY_PATH.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=RUN_HISTORY_COLUMNS)
                if write_header:
                    writer.writeheader()
                writer.writerow({column: row.get(column, "") for column in RUN_HISTORY_COLUMNS})
