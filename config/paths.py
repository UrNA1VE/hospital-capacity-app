"""Shared filesystem paths for the hospital capacity application."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONTAINER_DATA_ROOT = PROJECT_ROOT / "data" / "container"
RAW_DATA_DIR = CONTAINER_DATA_ROOT / "raw"
BACKUP_DATA_DIR = CONTAINER_DATA_ROOT / "backup"
REPORT_DATA_DIR = CONTAINER_DATA_ROOT / "reports"
LOG_DATA_DIR = CONTAINER_DATA_ROOT / "logs"

ETL_PREPARED_DIR = PROJECT_ROOT / "data" / "etl_prepared"
DASHBOARD_PREPARED_DIR = PROJECT_ROOT / "data" / "dashboard_prepared"
PREPARED_DATA_DIR = DASHBOARD_PREPARED_DIR

RUN_HISTORY_PATH = LOG_DATA_DIR / "run_history.csv"
EDIT_HISTORY_PATH = LOG_DATA_DIR / "edit_history.csv"

RAW_TABLE_PATHS = {
    "patients": RAW_DATA_DIR / "patients.csv",
    "admission_chart": RAW_DATA_DIR / "admission_chart.csv",
    "patient_events": RAW_DATA_DIR / "patient_events.csv",
    "facilities": RAW_DATA_DIR / "facilities.csv",
    "services": RAW_DATA_DIR / "services.csv",
    "units": RAW_DATA_DIR / "units.csv",
    "diagnoses": RAW_DATA_DIR / "diagnoses.csv",
    "capacity": RAW_DATA_DIR / "capacity.csv",
    "population_growth": RAW_DATA_DIR / "population_growth.csv",
}

ETL_PREPARED_TABLE_PATHS = {
    "visits": ETL_PREPARED_DIR / "visits.csv",
    "unit_changes": ETL_PREPARED_DIR / "unit_changes.csv",
}

DASHBOARD_TABLE_PATHS = {
    "daily": DASHBOARD_PREPARED_DIR / "daily.csv",
    "census": DASHBOARD_PREPARED_DIR / "census.csv",
    "pressure": DASHBOARD_PREPARED_DIR / "pressure.csv",
    "demand": DASHBOARD_PREPARED_DIR / "demand.csv",
    "current_demand": DASHBOARD_PREPARED_DIR / "current_demand.csv",
    "demographics": DASHBOARD_PREPARED_DIR / "demographics.csv",
    "projection": DASHBOARD_PREPARED_DIR / "projection.csv",
    "quality": DASHBOARD_PREPARED_DIR / "quality.csv",
    "facility_filters": DASHBOARD_PREPARED_DIR / "facility_filters.csv",
}

REPORT_PATHS = {
    "data_check_report": REPORT_DATA_DIR / "data_check_report.csv",
    "pipeline_result": REPORT_DATA_DIR / "pipeline_result.json",
    "incremental_runs": REPORT_DATA_DIR / "incremental_runs.csv",
    "latest_incremental_run": REPORT_DATA_DIR / "latest_incremental_run.json",
}

JOB_HISTORY_TABLE_PATHS = {
    "run_history": RUN_HISTORY_PATH,
    "edit_history": EDIT_HISTORY_PATH,
}

EDITABLE_RAW_FILE_NAMES = (
    "patients.csv",
    "admission_chart.csv",
    "patient_events.csv",
)

DASHBOARD_MART_REQUIRED_PATHS = [
    DASHBOARD_TABLE_PATHS["daily"],
    DASHBOARD_TABLE_PATHS["pressure"],
    DASHBOARD_TABLE_PATHS["current_demand"],
    DASHBOARD_TABLE_PATHS["projection"],
    DASHBOARD_TABLE_PATHS["facility_filters"],
]

PATIENT_JOURNEY_REQUIRED_PATHS = [
    ETL_PREPARED_TABLE_PATHS["visits"],
    ETL_PREPARED_TABLE_PATHS["unit_changes"],
    RAW_TABLE_PATHS["facilities"],
    RAW_TABLE_PATHS["services"],
    RAW_TABLE_PATHS["units"],
    RAW_TABLE_PATHS["diagnoses"],
    RAW_TABLE_PATHS["admission_chart"],
    RAW_TABLE_PATHS["patient_events"],
]

ANALYSIS_REQUIRED_PATHS = [
    DASHBOARD_TABLE_PATHS["daily"],
    ETL_PREPARED_TABLE_PATHS["visits"],
    ETL_PREPARED_TABLE_PATHS["unit_changes"],
    RAW_TABLE_PATHS["facilities"],
    RAW_TABLE_PATHS["services"],
    RAW_TABLE_PATHS["units"],
    RAW_TABLE_PATHS["diagnoses"],
    RAW_TABLE_PATHS["population_growth"],
]

RUNTIME_REQUIRED_PATHS = [
    RAW_TABLE_PATHS["patients"],
    RAW_TABLE_PATHS["admission_chart"],
    RAW_TABLE_PATHS["patient_events"],
    RAW_TABLE_PATHS["capacity"],
    ETL_PREPARED_TABLE_PATHS["visits"],
    ETL_PREPARED_TABLE_PATHS["unit_changes"],
    DASHBOARD_TABLE_PATHS["daily"],
    DASHBOARD_TABLE_PATHS["pressure"],
    DASHBOARD_TABLE_PATHS["current_demand"],
    DASHBOARD_TABLE_PATHS["projection"],
    DASHBOARD_TABLE_PATHS["facility_filters"],
    RUN_HISTORY_PATH,
]

RAW_STATE_PATHS = [
    RAW_TABLE_PATHS["patients"],
    RAW_TABLE_PATHS["admission_chart"],
    RAW_TABLE_PATHS["patient_events"],
    RAW_TABLE_PATHS["capacity"],
]

PREPARED_STATE_PATHS = [
    ETL_PREPARED_TABLE_PATHS["visits"],
    ETL_PREPARED_TABLE_PATHS["unit_changes"],
    DASHBOARD_TABLE_PATHS["daily"],
    DASHBOARD_TABLE_PATHS["pressure"],
    DASHBOARD_TABLE_PATHS["current_demand"],
    DASHBOARD_TABLE_PATHS["projection"],
]
