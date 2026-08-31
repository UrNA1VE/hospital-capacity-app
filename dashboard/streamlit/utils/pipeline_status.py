"""Pipeline table metadata, freshness, and status helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from etl.pipeline.job_history import load_job_history
from config.paths import (
    DASHBOARD_TABLE_PATHS,
    ETL_PREPARED_TABLE_PATHS,
    PROJECT_ROOT,
    RAW_TABLE_PATHS,
    REPORT_PATHS,
)
from utils.csv_io import read_csv_profile

RAW_PIPELINE_TABLES = {
    "patients": ("patient_id", ("registration_date",)),
    "admission_chart": ("visit_id", ("admission_ts",)),
    "patient_events": ("event_id", ("event_ts",)),
    "capacity": ("capacity_date", ("capacity_date",)),
}
ETL_PIPELINE_TABLES = {
    "visits": ("visit_id", ("admission_ts", "discharge_ts")),
    "unit_changes": ("unit_change_id", ("event_ts",)),
}
DASHBOARD_PIPELINE_TABLES = {
    "daily": ("calendar_date", ("calendar_date",)),
    "census": ("hour_ts", ("hour_ts",)),
    "pressure": ("calendar_date", ("calendar_date",)),
    "quality": ("check_name", ()),
}


def profile_csvs(
    table_paths: dict[str, Path],
    table_config: dict[str, tuple[str, tuple[str, ...]]],
) -> pd.DataFrame:
    rows = []
    for table_name, (_, freshness_columns) in table_config.items():
        path = table_paths[table_name]
        if not path.exists():
            rows.append(
                {
                    "table": table_name,
                    "rows": "missing",
                    "columns": "missing",
                    "freshness": "missing",
                }
            )
            continue
        profile = read_csv_profile(str(path), freshness_columns, path.stat().st_mtime_ns)
        rows.append(
            {
                "table": table_name,
                "rows": profile["rows"],
                "columns": profile["columns"],
                "freshness": profile["latest"],
            }
        )
    return pd.DataFrame(rows)


def dashboard_mart_end_date() -> str:
    daily_path = DASHBOARD_TABLE_PATHS["daily"]
    if daily_path.exists():
        daily_profile = read_csv_profile(str(daily_path), ("calendar_date",), daily_path.stat().st_mtime_ns)
        if daily_profile["latest"] != "n/a":
            return str(daily_profile["latest"])

    raw_capacity_path = RAW_TABLE_PATHS["capacity"]
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
        DASHBOARD_TABLE_PATHS,
        {name: (key, ()) for name, (key, _) in DASHBOARD_PIPELINE_TABLES.items()},
    )
    profile["freshness"] = end_date
    return profile


def load_quality_summary() -> tuple[pd.DataFrame, str]:
    quality_path = DASHBOARD_TABLE_PATHS["quality"]
    report_path = REPORT_PATHS["data_check_report"]
    if quality_path.exists():
        return pd.read_csv(quality_path), str(quality_path.relative_to(PROJECT_ROOT))
    if report_path.exists():
        return pd.read_csv(report_path), str(report_path.relative_to(PROJECT_ROOT))
    return pd.DataFrame(columns=["check_name", "severity", "issue_count", "details", "status"]), "not generated"


def load_incremental_summary() -> dict[str, object] | None:
    path = REPORT_PATHS["latest_incremental_run"]
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"status": "unreadable", "path": str(path.relative_to(PROJECT_ROOT))}


def load_run_history() -> pd.DataFrame:
    return load_job_history()
