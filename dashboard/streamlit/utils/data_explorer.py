"""Data Explorer helpers for table profiling and checks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from config.paths import RAW_DATA_DIR
from utils.csv_io import format_date
from utils.pipeline_status import load_quality_summary
from utils.table_catalog import LAYERS, RAW_TABLES, TableMeta


def table_path(folder: Path, meta: TableMeta) -> Path:
    return folder / meta.file_name


@st.cache_data
def _read_table_cached(path: str, modified_ns: int) -> pd.DataFrame:
    return pd.read_csv(path)


def read_table(path: Path) -> pd.DataFrame:
    return _read_table_cached(str(path), path.stat().st_mtime_ns) if path.exists() else pd.DataFrame()


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


def layer_summary(folder: Path, tables: dict[str, TableMeta]) -> int:
    return sum(table_path(folder, meta).exists() for meta in tables.values())
