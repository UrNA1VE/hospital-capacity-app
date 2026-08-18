"""Read and manage ETL job history files."""

from __future__ import annotations

import pandas as pd

from etl.pipeline.paths import EDIT_HISTORY_PATH, RUN_HISTORY_PATH


JOB_HISTORY_COLUMNS = ["job_id", "job_type", "status", "started_at", "finished_at", "duration_seconds"]


def load_job_history() -> pd.DataFrame:
    if not RUN_HISTORY_PATH.exists():
        return pd.DataFrame(columns=JOB_HISTORY_COLUMNS)

    history = pd.read_csv(RUN_HISTORY_PATH)
    if history.empty:
        return pd.DataFrame(columns=history.columns)

    if "started_at" in history.columns:
        history = history.assign(_started_at_sort=pd.to_datetime(history["started_at"], errors="coerce"))
        history = history.sort_values("_started_at_sort", ascending=False).drop(columns=["_started_at_sort"])

    return history.reset_index(drop=True)


def clear_job_history() -> None:
    for path in [RUN_HISTORY_PATH, EDIT_HISTORY_PATH]:
        if path.exists():
            path.unlink()
