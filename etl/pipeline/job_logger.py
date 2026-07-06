"""Lightweight job audit logging for container ETL actions."""

from __future__ import annotations

import json
import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTAINER_DATA_ROOT = PROJECT_ROOT / "data" / "container"
LOG_DATA_DIR = CONTAINER_DATA_ROOT / "logs"
RUN_HISTORY_PATH = LOG_DATA_DIR / "run_history.csv"
RUN_HISTORY_COLUMNS = [
    "job_id",
    "job_type",
    "status",
    "started_at",
    "finished_at",
    "duration_seconds",
    "params_json",
    "metrics_json",
    "message",
]


def _json_dumps(value: dict[str, object]) -> str:
    return json.dumps(value, default=str, sort_keys=True)


@dataclass
class EtlJob:
    """Context manager that records one user-triggered ETL job."""

    job_type: str
    params: dict[str, object] | None = None
    enabled: bool = True
    job_id: str = field(init=False)
    started_at: datetime = field(init=False)
    metrics: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        suffix = uuid4().hex[:8].upper()
        self.job_id = f"JOB-{timestamp}-{suffix}"

    def __enter__(self) -> "EtlJob":
        self.started_at = datetime.now().replace(microsecond=0)
        return self

    def set_metrics(self, **metrics: object) -> None:
        self.metrics.update(metrics)

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        finished_at = datetime.now().replace(microsecond=0)
        status = "success" if exc_type is None else "failed"
        message = "" if exc_value is None else str(exc_value)
        self._append_history(
            {
                "job_id": self.job_id,
                "job_type": self.job_type,
                "status": status,
                "started_at": self.started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "duration_seconds": int((finished_at - self.started_at).total_seconds()),
                "params_json": _json_dumps(self.params or {}),
                "metrics_json": _json_dumps(self.metrics),
                "message": message,
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
