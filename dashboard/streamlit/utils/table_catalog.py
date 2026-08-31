"""Table metadata used by the Data Explorer page."""

from __future__ import annotations

from dataclasses import dataclass

from config.paths import DASHBOARD_PREPARED_DIR, ETL_PREPARED_DIR, RAW_DATA_DIR
from config.paths import LOG_DATA_DIR


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
