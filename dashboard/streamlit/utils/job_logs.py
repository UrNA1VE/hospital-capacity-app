"""Reusable Job Logs popover for Streamlit pages."""

from __future__ import annotations

import shutil

import pandas as pd
import streamlit as st

from etl.pipeline.job_logger import EDIT_HISTORY_PATH, RUN_HISTORY_PATH
from utils.database import PROJECT_ROOT


JOB_LOG_COLUMNS = ["job_id", "job_type", "status", "started_at", "finished_at", "duration_seconds"]
RUNTIME_CLEANUP_SESSION_KEY = "runtime_data_cleared_on_open_v2"
RUNTIME_DATA_DIRS = [
    PROJECT_ROOT / "data" / "container",
    PROJECT_ROOT / "data" / "etl_prepared",
    PROJECT_ROOT / "data" / "dashboard_prepared",
]


def load_job_history() -> pd.DataFrame:
    if not RUN_HISTORY_PATH.exists():
        return pd.DataFrame(columns=JOB_LOG_COLUMNS)

    history = pd.read_csv(RUN_HISTORY_PATH)
    if history.empty:
        return pd.DataFrame(columns=history.columns)

    if "started_at" in history.columns:
        history = history.assign(_started_at_sort=pd.to_datetime(history["started_at"], errors="coerce"))
        history = history.sort_values("_started_at_sort", ascending=False).drop(columns=["_started_at_sort"])

    return history.reset_index(drop=True)


def clear_job_history() -> None:
    for path in [RUN_HISTORY_PATH, EDIT_HISTORY_PATH]:
        if path.exists():
            path.unlink()


def clear_runtime_data() -> None:
    for folder in RUNTIME_DATA_DIRS:
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)


def clear_runtime_data_once_on_open() -> None:
    if RUNTIME_CLEANUP_SESSION_KEY in st.session_state:
        return
    clear_runtime_data()
    st.session_state[RUNTIME_CLEANUP_SESSION_KEY] = True


def render_job_logs(limit: int = 50) -> None:
    clear_runtime_data_once_on_open()
    with st.popover("Job Logs", use_container_width=True):
        history = load_job_history()
        st.markdown("**Job Logs**")
        st.caption("Newest jobs first.")

        if history.empty:
            st.info("No job history yet. Run Initialize Dataset, Incremental Run, or submit an editor change.")
            st.caption(str(RUN_HISTORY_PATH.relative_to(PROJECT_ROOT)))
            return

        st.dataframe(
            history.head(limit),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Showing {min(len(history), limit):,} of {len(history):,} jobs")
        st.caption(str(RUN_HISTORY_PATH.relative_to(PROJECT_ROOT)))


def render_page_header(title: str, caption: str | None = None) -> None:
    title_col, logs_col = st.columns([1, 0.18])
    with title_col:
        st.title(title)
        if caption:
            st.caption(caption)
    with logs_col:
        st.write("")
        render_job_logs()
