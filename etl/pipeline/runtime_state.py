"""Runtime state helpers for the Streamlit app."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from etl.pipeline.job_history import load_job_history
from config.paths import (
    DASHBOARD_TABLE_PATHS,
    PREPARED_STATE_PATHS,
    RAW_STATE_PATHS,
    RUNTIME_REQUIRED_PATHS,
)


@dataclass(frozen=True)
class RuntimeSummary:
    data_exists: bool
    data_dirty: bool
    latest_data_date: str
    last_job_status: str
    last_job_type: str
    job_count: int


def runtime_data_exists() -> bool:
    """Return whether the app has enough generated data to render all pages."""
    return all(path.exists() for path in RUNTIME_REQUIRED_PATHS)


def data_dirty() -> bool:
    """Return whether raw source files are newer than prepared outputs."""
    existing_raw = [path for path in RAW_STATE_PATHS if path.exists()]
    existing_prepared = [path for path in PREPARED_STATE_PATHS if path.exists()]
    if not existing_raw or not existing_prepared:
        return False

    latest_raw_mtime = max(path.stat().st_mtime_ns for path in existing_raw)
    latest_prepared_mtime = max(path.stat().st_mtime_ns for path in existing_prepared)
    return latest_raw_mtime > latest_prepared_mtime


def latest_data_date() -> str:
    daily_path = DASHBOARD_TABLE_PATHS["daily"]
    if not daily_path.exists():
        return "n/a"

    daily = pd.read_csv(daily_path, usecols=["calendar_date"])
    dates = pd.to_datetime(daily["calendar_date"], errors="coerce")
    return dates.max().date().isoformat() if dates.notna().any() else "n/a"


def runtime_summary() -> RuntimeSummary:
    history = load_job_history()
    last_job = history.iloc[0] if not history.empty else {}
    return RuntimeSummary(
        data_exists=runtime_data_exists(),
        data_dirty=data_dirty(),
        latest_data_date=latest_data_date(),
        last_job_status=str(last_job.get("status", "not run")),
        last_job_type=str(last_job.get("job_type", "not run")),
        job_count=len(history),
    )
