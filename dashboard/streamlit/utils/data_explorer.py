"""Data Explorer helpers for table metadata, profiling, and checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from etl.pipeline.job_logger import LOG_DATA_DIR
from utils.database import DASHBOARD_PREPARED_DIR, ETL_PREPARED_DIR, RAW_DATA_DIR, format_date, load_quality_summary


@dataclass(frozen=True)
class TableMeta:
    file_name: str
    layer: str
    grain: str
    description: str
    primary_key: str | None = None
    freshness_column: str | None = None
    required_columns: tuple[str, ...] = ()
    foreign_keys: tuple[tuple[str, str, str], ...] = ()
    allowed_values: dict[str, tuple[str, ...]] | None = None


RAW_TABLES = {
    "patients": TableMeta(
        "patients.csv",
        "Raw Data",
        "One row per synthetic patient.",
        "Patient demographics and first registration date.",
        primary_key="patient_id",
        freshness_column="registration_date",
        required_columns=("patient_id", "registration_date", "age", "gender", "region"),
    ),
    "admission_chart": TableMeta(
        "admission_chart.csv",
        "Raw Data",
        "One row per encounter admission/start state.",
        "Admission facts used with patient_events to derive visit-level analytics.",
        primary_key="visit_id",
        freshness_column="admission_ts",
        required_columns=(
            "visit_id",
            "patient_id",
            "facility_id",
            "admitted_unit_id",
            "admitted_service_id",
            "admitted_diagnosis_code",
            "admission_ts",
            "admission_type",
        ),
        foreign_keys=(
            ("patient_id", "patients", "patient_id"),
            ("facility_id", "facilities", "facility_id"),
            ("admitted_service_id", "services", "service_id"),
            ("admitted_unit_id", "units", "unit_id"),
            ("admitted_diagnosis_code", "diagnoses", "diagnosis_code"),
        ),
    ),
    "patient_events": TableMeta(
        "patient_events.csv",
        "Raw Data",
        "One row per event after admission.",
        "Event-level source of truth for location, service, diagnosis, and discharge changes.",
        primary_key="event_id",
        freshness_column="event_ts",
        required_columns=("event_id", "visit_id", "patient_id", "event_ts", "type", "value", "facility_id"),
        foreign_keys=(("visit_id", "admission_chart", "visit_id"), ("patient_id", "patients", "patient_id")),
        allowed_values={"type": ("location", "service", "diagnosis", "discharge")},
    ),
    "capacity": TableMeta(
        "capacity.csv",
        "Raw Data",
        "One row per facility, service, and date.",
        "Funded/staffed capacity used as the denominator for pressure and demand analysis.",
        freshness_column="capacity_date",
        required_columns=("capacity_date", "facility_id", "service_id", "staffed_beds"),
        foreign_keys=(("facility_id", "facilities", "facility_id"), ("service_id", "services", "service_id")),
    ),
    "facilities": TableMeta(
        "facilities.csv",
        "Raw Data",
        "One row per facility.",
        "Reference data for facility names and regions.",
        primary_key="facility_id",
        required_columns=("facility_id", "facility_name", "region"),
    ),
    "units": TableMeta(
        "units.csv",
        "Raw Data",
        "One row per physical unit.",
        "Reference data mapping units to facilities.",
        primary_key="unit_id",
        required_columns=("unit_id", "facility_id", "unit_name"),
        foreign_keys=(("facility_id", "facilities", "facility_id"),),
    ),
    "services": TableMeta(
        "services.csv",
        "Raw Data",
        "One row per clinical service.",
        "Reference data for service labels.",
        primary_key="service_id",
        required_columns=("service_id", "service_name"),
    ),
    "diagnoses": TableMeta(
        "diagnoses.csv",
        "Raw Data",
        "One row per synthetic diagnosis code.",
        "Reference data mapping diagnosis codes to services.",
        primary_key="diagnosis_code",
        required_columns=("diagnosis_code", "diagnosis_name", "service_id"),
        foreign_keys=(("service_id", "services", "service_id"),),
    ),
    "population_growth": TableMeta(
        "population_growth.csv",
        "Raw Data",
        "One row per region, age group, gender, and projection year.",
        "Planning input used by service projection models.",
        required_columns=("region", "age_group", "gender", "year", "growth_index"),
    ),
}

ETL_TABLES = {
    "visits": TableMeta(
        "visits.csv",
        "ETL Prepared Layer",
        "One row per derived encounter.",
        "Visit-level table rebuilt from admission_chart and patient_events.",
        primary_key="visit_id",
        freshness_column="discharge_ts",
        required_columns=("visit_id", "patient_id", "facility_id", "service_id", "admission_ts", "discharge_ts"),
    ),
    "unit_changes": TableMeta(
        "unit_changes.csv",
        "ETL Prepared Layer",
        "One row per derived unit/location state change.",
        "Unit movement table rebuilt from admission starting units and location events.",
        primary_key="unit_change_id",
        freshness_column="event_ts",
        required_columns=("unit_change_id", "visit_id", "event_ts", "facility_id", "unit_id"),
        foreign_keys=(("visit_id", "admission_chart", "visit_id"), ("facility_id", "facilities", "facility_id")),
    ),
}

DASHBOARD_TABLES = {
    "daily": TableMeta(
        "daily.csv",
        "Dashboard Mart",
        "One row per date, facility, and service.",
        "Daily census, capacity, and utilization mart used by dashboard charts.",
        freshness_column="calendar_date",
        required_columns=("calendar_date", "facility_name", "service_name", "peak_census", "staffed_beds"),
    ),
    "census": TableMeta(
        "census.csv",
        "Dashboard Mart",
        "One row per hour, facility, and service.",
        "Hourly census mart.",
        freshness_column="hour_ts",
        required_columns=("hour_ts", "facility_name", "service_name", "census"),
    ),
    "pressure": TableMeta(
        "pressure.csv",
        "Dashboard Mart",
        "One row per date, facility, and service.",
        "Capacity pressure categories and threshold flags.",
        freshness_column="calendar_date",
        required_columns=("calendar_date", "facility_name", "service_name", "peak_utilization", "pressure_level"),
    ),
    "demand": TableMeta(
        "demand.csv",
        "Dashboard Mart",
        "One row per planning year, facility, and service.",
        "Projected demand without service-planning adjustments.",
        required_columns=("year", "facility_name", "service_name", "demand", "funded_capacity"),
    ),
    "current_demand": TableMeta(
        "current_demand.csv",
        "Dashboard Mart",
        "One row per facility and service.",
        "Current demand compared with funded capacity.",
        required_columns=("facility_name", "service_name", "demand", "funded_capacity", "variance"),
    ),
    "demographics": TableMeta(
        "demographics.csv",
        "Dashboard Mart",
        "One row per facility, service, age group, gender, and region.",
        "Patient-day demographics used by projection models.",
        required_columns=("facility_name", "service_name", "age_group", "gender", "region", "patient_days"),
    ),
    "projection": TableMeta(
        "projection.csv",
        "Dashboard Mart",
        "One row per year, facility, and service.",
        "Projected bed needs before and after service-planning adjustments.",
        required_columns=("year", "facility_name", "service_name", "projection", "adjusted_projection"),
    ),
    "savings": TableMeta(
        "savings.csv",
        "Dashboard Mart",
        "One row per facility, service, and saving algorithm.",
        "Potential demand reduction from synthetic service-planning algorithms.",
        required_columns=("facility_name", "service_name", "saving_type", "demand_reduction"),
    ),
    "quality": TableMeta(
        "quality.csv",
        "Dashboard Mart",
        "One row per quality check.",
        "Dashboard-facing data quality report.",
        required_columns=("check_name", "severity", "issue_count", "status"),
    ),
}

JOB_HISTORY_TABLES = {
    "run_history": TableMeta(
        "run_history.csv",
        "Job History",
        "One row per logged ETL job.",
        "Full audit trail for initial dataset, incremental runs, user edits, and undo actions.",
        primary_key="job_id",
        freshness_column="started_at",
        required_columns=("job_id", "job_type", "status", "started_at", "finished_at", "duration_seconds", "message", "changes"),
        allowed_values={"status": ("success", "failed")},
    ),
}

LAYERS = {
    "Raw Data": (RAW_DATA_DIR, RAW_TABLES),
    "ETL Prepared Layer": (ETL_PREPARED_DIR, ETL_TABLES),
    "Dashboard Mart": (DASHBOARD_PREPARED_DIR, DASHBOARD_TABLES),
    "Job History": (LOG_DATA_DIR, JOB_HISTORY_TABLES),
}


def table_path(folder: Path, meta: TableMeta) -> Path:
    return folder / meta.file_name


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def latest_value(frame: pd.DataFrame, column: str | None) -> str:
    if not column or column not in frame.columns:
        return "n/a"
    values = pd.to_datetime(frame[column], errors="coerce")
    return format_date(values.max()) if values.notna().any() else "n/a"


def add_check(rows: list[dict[str, object]], name: str, passed: bool, details: str) -> None:
    rows.append(
        {
            "check": name,
            "status": "pass" if passed else "fail",
            "details": details,
        }
    )


def quality_checks(
    frame: pd.DataFrame,
    meta: TableMeta,
    raw_tables: dict[str, TableMeta],
    raw_data_dir: Path,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    add_check(rows, "Table is not empty", not frame.empty, f"{len(frame):,} rows")

    missing_columns = [column for column in meta.required_columns if column not in frame.columns]
    add_check(
        rows,
        "Required columns present",
        not missing_columns,
        "All required columns found" if not missing_columns else f"Missing: {', '.join(missing_columns)}",
    )

    if meta.primary_key and meta.primary_key in frame.columns:
        null_count = int(frame[meta.primary_key].isna().sum())
        duplicate_count = int(frame[meta.primary_key].duplicated().sum())
        add_check(rows, "Primary key not null", null_count == 0, f"{null_count:,} null keys")
        add_check(rows, "Primary key unique", duplicate_count == 0, f"{duplicate_count:,} duplicate keys")

    if meta.freshness_column and meta.freshness_column in frame.columns:
        valid_dates = pd.to_datetime(frame[meta.freshness_column], errors="coerce").notna()
        invalid_count = int((~valid_dates).sum())
        add_check(rows, "Freshness column valid", invalid_count == 0, f"{invalid_count:,} invalid dates")

    if meta.allowed_values:
        for column, allowed_values in meta.allowed_values.items():
            if column in frame.columns:
                invalid_count = int((~frame[column].isin(allowed_values)).sum())
                add_check(rows, f"{column} values allowed", invalid_count == 0, f"{invalid_count:,} invalid values")

    for column, target_table, target_column in meta.foreign_keys:
        if column not in frame.columns or target_table not in raw_tables:
            continue
        target_path = raw_data_dir / raw_tables[target_table].file_name
        target = read_table(target_path)
        if target.empty or target_column not in target.columns:
            add_check(rows, f"{column} references {target_table}", False, "Reference table unavailable")
            continue
        missing_count = int((~frame[column].dropna().isin(target[target_column].dropna())).sum())
        add_check(
            rows,
            f"{column} references {target_table}",
            missing_count == 0,
            f"{missing_count:,} unmatched values",
        )

    return pd.DataFrame(rows)


def matching_pipeline_checks(table_name: str) -> pd.DataFrame:
    quality, _ = load_quality_summary()
    if quality.empty:
        return quality
    text = quality.astype(str).agg(" ".join, axis=1).str.lower()
    return quality[text.str.contains(table_name.lower(), regex=False)].reset_index(drop=True)


def job_history_preview(frame: pd.DataFrame) -> pd.DataFrame:
    display_columns = [
        "job_id",
        "job_type",
        "status",
        "started_at",
        "finished_at",
        "duration_seconds",
    ]
    preview = frame.head(5).copy()
    return preview[[column for column in display_columns if column in preview.columns]]


def layer_summary(folder: Path, tables: dict[str, TableMeta]) -> tuple[int, int]:
    existing_paths = [table_path(folder, meta) for meta in tables.values() if table_path(folder, meta).exists()]
    total_rows = sum(len(read_table(path)) for path in existing_paths)
    return len(existing_paths), total_rows
