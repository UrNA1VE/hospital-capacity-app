"""Dashboard data access and CSV profiling utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from etl.pipeline.job_history import load_job_history
from etl.pipeline.paths import (
    DASHBOARD_PREPARED_DIR,
    ETL_PREPARED_DIR,
    PROJECT_ROOT,
    RAW_DATA_DIR,
    REPORT_DATA_DIR,
)
from etl.pipeline.transform_helpers import (
    reporting_window as _reporting_window,
    unit_changes_overlapping_window as _unit_changes_overlapping_window,
    visits_overlapping_window as _visits_overlapping_window,
)

PREPARED_DATA_DIR = DASHBOARD_PREPARED_DIR
EVENT_SOURCE_FILES = {"patients.csv", "admission_chart.csv", "patient_events.csv"}
REFERENCE_SOURCE_FILES = {
    "capacity.csv",
    "diagnoses.csv",
    "facilities.csv",
    "population_growth.csv",
    "services.csv",
    "units.csv",
}
AGGREGATED_SOURCE_FILES = {
    "capacity.csv",
    "census.csv",
    "current_demand.csv",
    "daily.csv",
    "demand.csv",
    "demographics.csv",
    "pressure.csv",
    "projection.csv",
    "quality.csv",
    "savings.csv",
}
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


@st.cache_data
def read_csv_preview(path: str, modified_ns: int) -> pd.DataFrame:
    return pd.read_csv(path).head(100)


def format_date(value: object) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    return timestamp.date().isoformat() if pd.notna(timestamp) else "n/a"


@st.cache_data
def read_csv_profile(path: str, freshness_columns: tuple[str, ...], modified_ns: int) -> dict[str, object]:
    frame = pd.read_csv(path)
    latest_values = []
    for column in freshness_columns:
        if column in frame.columns:
            values = pd.to_datetime(frame[column], errors="coerce")
            if values.notna().any():
                latest_values.append(values.max())

    latest = max(latest_values) if latest_values else pd.NaT
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "latest": format_date(latest),
    }


def list_csvs(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.csv")) if folder.exists() else []


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
    daily_path = PREPARED_DATA_DIR / "daily.csv"
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
    profile = profile_csvs(PREPARED_DATA_DIR, {name: (key, ()) for name, (key, _) in DASHBOARD_PIPELINE_FILES.items()})
    profile["freshness"] = end_date
    return profile


def load_quality_summary() -> tuple[pd.DataFrame, str]:
    quality_path = PREPARED_DATA_DIR / "quality.csv"
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


def read_prepared_dashboard_sources() -> dict[str, pd.DataFrame]:
    required_files = [
        DASHBOARD_PREPARED_DIR / "daily.csv",
        DASHBOARD_PREPARED_DIR / "pressure.csv",
        DASHBOARD_PREPARED_DIR / "quality.csv",
        DASHBOARD_PREPARED_DIR / "capacity.csv",
        DASHBOARD_PREPARED_DIR / "census.csv",
        DASHBOARD_PREPARED_DIR / "savings.csv",
        DASHBOARD_PREPARED_DIR / "demographics.csv",
        DASHBOARD_PREPARED_DIR / "demand.csv",
        DASHBOARD_PREPARED_DIR / "current_demand.csv",
        DASHBOARD_PREPARED_DIR / "projection.csv",
        DASHBOARD_PREPARED_DIR / "facility_filters.csv",
        ETL_PREPARED_DIR / "visits.csv",
        RAW_DATA_DIR / "facilities.csv",
        RAW_DATA_DIR / "services.csv",
        RAW_DATA_DIR / "units.csv",
        RAW_DATA_DIR / "diagnoses.csv",
        RAW_DATA_DIR / "population_growth.csv",
        RAW_DATA_DIR / "capacity.csv",
        RAW_DATA_DIR / "admission_chart.csv",
        RAW_DATA_DIR / "patient_events.csv",
    ]
    if not all(path.exists() for path in required_files):
        raise FileNotFoundError("Prepared dashboard data is missing.")

    visits = pd.read_csv(ETL_PREPARED_DIR / "visits.csv", parse_dates=["admission_ts", "discharge_ts"])
    admission_chart = pd.read_csv(RAW_DATA_DIR / "admission_chart.csv", parse_dates=["admission_ts"])
    patient_events = pd.read_csv(RAW_DATA_DIR / "patient_events.csv", parse_dates=["event_ts"])
    unit_changes = pd.concat(
        [
            admission_chart[
                ["visit_id", "admission_ts", "facility_id", "admitted_unit_id"]
            ].rename(
                columns={
                    "admission_ts": "event_ts",
                    "admitted_unit_id": "unit_id",
                }
            ).assign(unit_change_id=lambda frame: "ADM-" + frame["visit_id"].astype(str)),
            patient_events[patient_events["type"] == "location"]
            .rename(columns={"event_id": "unit_change_id", "value": "unit_id"})
            [["unit_change_id", "visit_id", "event_ts", "facility_id", "unit_id"]],
        ],
        ignore_index=True,
    )
    unit_changes["event_ts"] = pd.to_datetime(unit_changes["event_ts"], errors="coerce")
    unit_changes = unit_changes.sort_values(["visit_id", "event_ts", "unit_change_id"]).reset_index(drop=True)

    return {
        "daily": pd.read_csv(DASHBOARD_PREPARED_DIR / "daily.csv", parse_dates=["calendar_date"]),
        "pressure": pd.read_csv(DASHBOARD_PREPARED_DIR / "pressure.csv", parse_dates=["calendar_date"]),
        "quality": pd.read_csv(DASHBOARD_PREPARED_DIR / "quality.csv"),
        "capacity": pd.read_csv(DASHBOARD_PREPARED_DIR / "capacity.csv"),
        "census": pd.read_csv(DASHBOARD_PREPARED_DIR / "census.csv"),
        "savings": pd.read_csv(DASHBOARD_PREPARED_DIR / "savings.csv"),
        "demographics": pd.read_csv(DASHBOARD_PREPARED_DIR / "demographics.csv"),
        "demand": pd.read_csv(DASHBOARD_PREPARED_DIR / "demand.csv"),
        "current_demand": pd.read_csv(DASHBOARD_PREPARED_DIR / "current_demand.csv"),
        "projection": pd.read_csv(DASHBOARD_PREPARED_DIR / "projection.csv"),
        "facility_filters": pd.read_csv(DASHBOARD_PREPARED_DIR / "facility_filters.csv"),
        "visits": visits,
        "raw_visits": visits.copy(),
        "admission_chart": admission_chart,
        "facilities": pd.read_csv(RAW_DATA_DIR / "facilities.csv"),
        "services": pd.read_csv(RAW_DATA_DIR / "services.csv"),
        "units": pd.read_csv(RAW_DATA_DIR / "units.csv"),
        "unit_changes": unit_changes,
        "diagnoses": pd.read_csv(RAW_DATA_DIR / "diagnoses.csv"),
        "population_growth": pd.read_csv(RAW_DATA_DIR / "population_growth.csv"),
        "raw_capacity": pd.read_csv(RAW_DATA_DIR / "capacity.csv", parse_dates=["capacity_date"]),
        "patient_events": patient_events,
    }


def build_sample_marts() -> dict[str, pd.DataFrame]:
    return read_prepared_dashboard_sources()


def load_dashboard_data() -> tuple[dict[str, pd.DataFrame], str]:
    return read_prepared_dashboard_sources(), "prepared container-local pipeline data"
