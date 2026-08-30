"""Pipeline table metadata, freshness, and status helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from etl.pipeline.job_history import load_job_history
from etl.pipeline.paths import DASHBOARD_PREPARED_DIR, PROJECT_ROOT, RAW_DATA_DIR, REPORT_DATA_DIR
from utils.csv_io import read_csv_profile

RAW_PIPELINE_FILES = {
    "patients.csv": ("patient_id", ("registration_date",)),
    "admission_chart.csv": ("visit_id", ("admission_ts",)),
    "patient_events.csv": ("event_id", ("event_ts",)),
    "capacity.csv": ("capacity_date", ("capacity_date",)),
}
ETL_PIPELINE_FILES = {
    "visits.csv": ("visit_id", ("admission_ts", "discharge_ts")),
    "unit_changes.csv": ("unit_change_id", ("event_ts",)),
}
DASHBOARD_PIPELINE_FILES = {
    "daily.csv": ("calendar_date", ("calendar_date",)),
    "census.csv": ("hour_ts", ("hour_ts",)),
    "pressure.csv": ("calendar_date", ("calendar_date",)),
    "quality.csv": ("check_name", ()),
}


def profile_csvs(folder: Path, file_config: dict[str, tuple[str, tuple[str, ...]]]) -> pd.DataFrame:
    rows = []
    for file_name, (_, freshness_columns) in file_config.items():
        path = folder / file_name
        if not path.exists():
            rows.append(
                {
                    "table": file_name.removesuffix(".csv"),
                    "rows": "missing",
                    "columns": "missing",
                    "freshness": "missing",
                }
            )
            continue
        profile = read_csv_profile(str(path), freshness_columns, path.stat().st_mtime_ns)
        rows.append(
            {
                "table": file_name.removesuffix(".csv"),
                "rows": profile["rows"],
                "columns": profile["columns"],
                "freshness": profile["latest"],
            }
        )
    return pd.DataFrame(rows)


def dashboard_mart_end_date() -> str:
    daily_path = DASHBOARD_PREPARED_DIR / "daily.csv"
    if daily_path.exists():
        daily_profile = read_csv_profile(str(daily_path), ("calendar_date",), daily_path.stat().st_mtime_ns)
        if daily_profile["latest"] != "n/a":
            return str(daily_profile["latest"])

    raw_capacity_path = RAW_DATA_DIR / "capacity.csv"
    if raw_capacity_path.exists():
        capacity_profile = read_csv_profile(
            str(raw_capacity_path),
            ("capacity_date",),
            raw_capacity_path.stat().st_mtime_ns,
        )
        return str(capacity_profile["latest"])

    return "n/a"


def profile_dashboard_marts() -> pd.DataFrame:
    end_date = dashboard_mart_end_date()
    profile = profile_csvs(
        DASHBOARD_PREPARED_DIR,
        {name: (key, ()) for name, (key, _) in DASHBOARD_PIPELINE_FILES.items()},
    )
    profile["freshness"] = end_date
    return profile


def load_quality_summary() -> tuple[pd.DataFrame, str]:
    quality_path = DASHBOARD_PREPARED_DIR / "quality.csv"
    report_path = REPORT_DATA_DIR / "data_check_report.csv"
    if quality_path.exists():
        return pd.read_csv(quality_path), str(quality_path.relative_to(PROJECT_ROOT))
    if report_path.exists():
        return pd.read_csv(report_path), str(report_path.relative_to(PROJECT_ROOT))
    return pd.DataFrame(columns=["check_name", "severity", "issue_count", "details", "status"]), "not generated"


def load_incremental_summary() -> dict[str, object] | None:
    path = REPORT_DATA_DIR / "latest_incremental_run.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"status": "unreadable", "path": str(path.relative_to(PROJECT_ROOT))}


def load_run_history() -> pd.DataFrame:
    return load_job_history()
