"""Shared filesystem paths for the demo ETL runtime."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

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
