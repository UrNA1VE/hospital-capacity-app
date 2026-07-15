"""Streamlit report and data-viewer components."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from etl.pipeline.job_logger import RUN_HISTORY_PATH
from utils.database import (
    ETL_PIPELINE_FILES,
    ETL_PREPARED_DIR,
    PROJECT_ROOT,
    RAW_DATA_DIR,
    RAW_PIPELINE_FILES,
    format_date,
    list_csvs,
    load_incremental_summary,
    load_quality_summary,
    load_run_history,
    profile_csvs,
    profile_dashboard_marts,
    read_csv_preview,
    read_csv_profile,
)


def parse_json_value(raw_json: object) -> object:
    if pd.isna(raw_json) or raw_json == "":
        return None
    try:
        return json.loads(str(raw_json))
    except json.JSONDecodeError:
        return str(raw_json)


def render_job_messages(raw_message: object) -> None:
    messages = parse_json_value(raw_message)
    if messages is None:
        st.caption("None")
    elif isinstance(messages, list):
        for message in messages:
            st.caption(f"- {message}")
    else:
        st.caption(str(messages))


def render_job_changes(raw_changes: object) -> None:
    changes = parse_json_value(raw_changes)
    if changes is None:
        st.caption("None")
    else:
        st.json(changes, expanded=False)


def render_pipeline_status() -> None:
    st.subheader("Pipeline Status")
    raw_profile = profile_csvs(RAW_DATA_DIR, RAW_PIPELINE_FILES)
    etl_profile = profile_csvs(ETL_PREPARED_DIR, ETL_PIPELINE_FILES)
    dashboard_profile = profile_dashboard_marts()
    quality, quality_source = load_quality_summary()
    issue_total = int(pd.to_numeric(quality.get("issue_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    blocking_total = int(
        pd.to_numeric(
            quality.loc[quality.get("severity", pd.Series(dtype=str)).eq("error"), "issue_count"],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    ) if not quality.empty and "severity" in quality.columns and "issue_count" in quality.columns else 0
    latest_incremental = load_incremental_summary()

    health_col, freshness_col, incremental_col = st.columns(3)
    with health_col:
        st.metric("Data check issues", issue_total, delta=f"{blocking_total} blocking")
    with freshness_col:
        raw_freshness = raw_profile.loc[raw_profile["table"].eq("capacity"), "freshness"]
        st.metric("Latest date", raw_freshness.iloc[0] if not raw_freshness.empty else "n/a")
    with incremental_col:
        if latest_incremental:
            st.metric("Last incremental status", str(latest_incremental.get("status", "unknown")))
            if latest_incremental.get("simulated_end"):
                st.caption(f"Simulated through {format_date(latest_incremental['simulated_end'])}")
        else:
            st.metric("Last incremental status", "not run")

    profile_tab, check_tab, history_tab = st.tabs(["Layer Tables", "Data Checks", "Run History"])
    with profile_tab:
        raw_col, etl_col, mart_col = st.columns(3)
        with raw_col:
            st.caption("Raw source tables")
            st.dataframe(raw_profile, use_container_width=True, hide_index=True)
        with etl_col:
            st.caption("ETL prepared tables")
            st.dataframe(etl_profile, use_container_width=True, hide_index=True)
        with mart_col:
            st.caption("Dashboard marts")
            st.dataframe(dashboard_profile, use_container_width=True, hide_index=True)

    with check_tab:
        st.caption(f"Source: {quality_source}")
        if quality.empty:
            st.info("No data check report available yet.")
        elif issue_total:
            st.warning("One or more data checks require review.")
            st.dataframe(quality, use_container_width=True, hide_index=True)
        else:
            st.success("All included data checks passed.")
            st.dataframe(quality, use_container_width=True, hide_index=True)

    with history_tab:
        history = load_run_history()
        st.caption(f"Source: {RUN_HISTORY_PATH.relative_to(PROJECT_ROOT)}")
        if history.empty:
            st.info("No ETL jobs have been logged yet.")
        else:
            display_columns = [
                "job_id",
                "job_type",
                "status",
                "started_at",
                "duration_seconds",
                "message",
            ]
            st.dataframe(
                history[[column for column in display_columns if column in history.columns]],
                use_container_width=True,
                hide_index=True,
            )
            selected_job_id = st.selectbox("Job details", history["job_id"].tolist())
            selected_job = history.loc[history["job_id"].eq(selected_job_id)].iloc[0]
            detail_col, metric_col = st.columns(2)
            with detail_col:
                st.caption("Message")
                render_job_messages(selected_job.get("message", ""))
            with metric_col:
                st.caption("Changes")
                render_job_changes(selected_job.get("changes", ""))


def data_viewer(label: str, folder: Path, allowed_files: set[str] | None = None) -> None:
    files = list_csvs(folder)
    if allowed_files is not None:
        files = [path for path in files if path.name in allowed_files]
    if not files:
        st.info(f"No {label} files available yet.")
        return
    selected = st.selectbox(
        f"{label} file",
        files,
        format_func=lambda path: path.name,
        key=f"{label}-{folder}",
    )
    profile = read_csv_profile(str(selected), (), selected.stat().st_mtime_ns)
    st.caption(f"{selected.relative_to(PROJECT_ROOT)} | {profile['rows']} rows")
    st.dataframe(read_csv_preview(str(selected), selected.stat().st_mtime_ns), use_container_width=True, hide_index=True)
