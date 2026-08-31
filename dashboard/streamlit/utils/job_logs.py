"""Reusable Job Logs popover for Streamlit pages."""

from __future__ import annotations

import streamlit as st

from etl.pipeline.job_history import load_job_history
from config.paths import PROJECT_ROOT, RUN_HISTORY_PATH


def render_job_logs(limit: int = 50) -> None:
    with st.popover("Job Logs", width="stretch"):
        history = load_job_history()
        st.markdown("**Job Logs**")
        st.caption("Newest jobs first.")

        if history.empty:
            st.info("No job history yet. Run Initialize Dataset, Incremental Run, or submit an editor change.")
            st.caption(str(RUN_HISTORY_PATH.relative_to(PROJECT_ROOT)))
            return

        st.dataframe(
            history.head(limit),
            width="stretch",
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
