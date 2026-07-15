"""ETL control center for the hospital capacity analytics app."""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import bootstrap  # noqa: F401
from etl.pipeline.incremental_run import IncrementalDataError, etl_incremental
from etl.pipeline.initialize_demo_dataset import (
    EDIT_HISTORY_PATH,
    RUN_HISTORY_PATH,
    reset_demo_runtime,
    run_fake_data_pipeline,
)
from utils.database import PROJECT_ROOT, read_csv_preview, read_csv_profile


def clear_job_history() -> None:
    for path in [RUN_HISTORY_PATH, EDIT_HISTORY_PATH]:
        if path.exists():
            path.unlink()


if "job_history_cleared_on_open" not in st.session_state:
    clear_job_history()
    st.session_state["job_history_cleared_on_open"] = True


st.set_page_config(page_title="Hospital Capacity Analytics App", page_icon="🏥", layout="wide")

st.title("Hospital Capacity Analytics App")
st.caption(
    "Synthetic event-level healthcare data pipeline with incremental ETL, data quality checks, "
    "editable source records, and dashboard-ready analytics."
)

st.markdown(
    """
    <style>
    .page-card {
        min-height: 158px;
        border: 1px solid rgba(250, 250, 250, 0.14);
        border-radius: 8px;
        padding: 0.95rem;
        background: rgba(255, 255, 255, 0.035);
        margin-bottom: 0.7rem;
    }
    .page-title {
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .page-copy {
        color: rgba(250, 250, 250, 0.68);
        font-size: 0.9rem;
        line-height: 1.35;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.subheader("Demo Actions")
    seed = st.number_input("Seed", min_value=1, max_value=999999, value=42, step=1)
    initialize_col, incremental_col, reset_col = st.columns(3)

    with initialize_col:
        st.markdown("**Initialize Dataset**")
        st.caption("Create the initial synthetic month and rebuild every downstream table.")
        if st.button("Initialize Dataset", type="primary", use_container_width=True):
            with st.spinner("Generating raw data, validating sources, and building dashboard marts..."):
                result = run_fake_data_pipeline(seed=int(seed))
                read_csv_preview.clear()
                read_csv_profile.clear()
            st.success(
                f"Pipeline complete: {result.validation_status.upper()} "
                f"({result.validation_issue_count} blocking validation issues)."
            )
            st.caption(f"Raw: {Path(result.raw_dir).relative_to(PROJECT_ROOT)}")
            st.caption(f"Prepared: {Path(result.prepared_dir).relative_to(PROJECT_ROOT)}")

    with incremental_col:
        st.markdown("**Incremental Run**")
        st.caption("Append the next simulated day and refresh ETL/dashboard outputs.")
        if st.button("Incremental Run", use_container_width=True):
            with st.spinner("Appending next-day data and rebuilding dashboard marts..."):
                try:
                    log = etl_incremental(seed=int(seed), length=1)
                except (FileNotFoundError, IncrementalDataError, KeyError) as error:
                    st.error(f"Incremental run failed: {error}")
                else:
                    read_csv_preview.clear()
                    read_csv_profile.clear()
                    st.success("Incremental run complete.")
                    st.code(log, language="json")

    with reset_col:
        st.markdown("**Reset Demo**")
        st.caption("Clear generated runtime data and start a clean demo session.")
        if st.button("Reset Demo", use_container_width=True):
            reset_demo_runtime()
            clear_job_history()
            read_csv_preview.clear()
            read_csv_profile.clear()
            st.success("Demo runtime cleared. Generate initial data to start a new session.")

st.subheader("Pipeline Workflow")
st.caption("The workflow scales to show the full end-to-end pipeline at a glance.")
components.html(
    """
    <style>
      body {
        margin: 0;
        background: transparent;
        color: rgb(250, 250, 250);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      .pipeline-map {
        width: 100%;
      }
      .pipeline-canvas {
        position: relative;
        width: 100%;
        aspect-ratio: 1190 / 270;
        min-height: 210px;
        border: 1px solid rgba(250, 250, 250, 0.08);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.018);
      }
      .pipeline-lines {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
      }
      .pipeline-node {
        position: absolute;
        width: 13.1%;
        min-height: 54px;
        border: 1px solid rgba(250, 250, 250, 0.18);
        border-radius: 2px;
        padding: 0.55rem 0.65rem;
        background: rgba(255, 255, 255, 0.04);
        text-align: center;
        box-sizing: border-box;
      }
      .pipeline-node.wide {
        width: 15.6%;
      }
      .pipeline-title {
        font-weight: 700;
        font-size: clamp(0.58rem, 1.05vw, 0.86rem);
        line-height: 1.2;
      }
      .pipeline-copy {
        color: rgba(250, 250, 250, 0.68);
        font-size: clamp(0.52rem, 0.9vw, 0.8rem);
        line-height: 1.35;
        margin-top: 0.25rem;
      }
    </style>
    <div class="pipeline-map">
        <div class="pipeline-canvas">
            <svg class="pipeline-lines" viewBox="0 0 1190 270" preserveAspectRatio="none">
                <defs>
                    <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                        <path d="M0,0 L8,4 L0,8 Z" fill="rgba(250,250,250,0.72)" />
                    </marker>
                </defs>
                <path d="M166 135 L210 135" stroke="rgba(250,250,250,0.62)" stroke-width="1.2" fill="none" marker-end="url(#arrowhead)" />
                <path d="M396 110 C430 88, 482 82, 552 82 L610 82" stroke="rgba(250,250,250,0.62)" stroke-width="1.2" fill="none" marker-end="url(#arrowhead)" />
                <path d="M396 160 C410 178, 418 185, 426 185" stroke="rgba(250,250,250,0.62)" stroke-width="1.2" fill="none" marker-end="url(#arrowhead)" />
                <path d="M796 82 C816 82, 820 116, 836 116" stroke="rgba(250,250,250,0.62)" stroke-width="1.2" fill="none" marker-end="url(#arrowhead)" />
                <path d="M612 185 L650 185" stroke="rgba(250,250,250,0.62)" stroke-width="1.2" fill="none" marker-end="url(#arrowhead)" />
                <path d="M806 185 C822 185, 822 166, 836 166" stroke="rgba(250,250,250,0.62)" stroke-width="1.2" fill="none" marker-end="url(#arrowhead)" />
                <path d="M992 141 L1034 141" stroke="rgba(250,250,250,0.62)" stroke-width="1.2" fill="none" marker-end="url(#arrowhead)" />
            </svg>

            <div class="pipeline-node" style="left: 2%; top: 40%;">
                <div class="pipeline-title">Initial / Incremental Run</div>
            </div>
            <div class="pipeline-node wide" style="left: 17.6%; top: 31.9%;">
                <div class="pipeline-title">Raw CSV Layer</div>
                <div class="pipeline-copy">patients, admissions,<br>events, capacity</div>
            </div>
            <div class="pipeline-node wide" style="left: 51.3%; top: 17.8%;">
                <div class="pipeline-title">Encounter ETL</div>
                <div class="pipeline-copy">derive visits +<br>unit_changes</div>
            </div>
            <div class="pipeline-node wide" style="left: 35.8%; top: 54.8%;">
                <div class="pipeline-title">Validation Layer</div>
                <div class="pipeline-copy">schema, keys, ranges,<br>references</div>
            </div>
            <div class="pipeline-node" style="left: 54.6%; top: 58.5%;">
                <div class="pipeline-title">Quality Report</div>
            </div>
            <div class="pipeline-node wide" style="left: 70.3%; top: 37.8%;">
                <div class="pipeline-title">Dashboard Marts</div>
                <div class="pipeline-copy">daily, census, pressure,<br>demand, projection</div>
            </div>
            <div class="pipeline-node" style="left: 86.9%; top: 37.8%;">
                <div class="pipeline-title">Streamlit App</div>
                <div class="pipeline-copy">status, explorer,<br>editor, dashboard</div>
            </div>
        </div>
    </div>
    """,
    height=240,
    scrolling=False,
)

st.subheader("App Pages")
page_cols = st.columns(4)
pages = [
    (
        "Data Explorer",
        "Inspect raw, ETL-prepared, and dashboard mart tables with freshness, grain, previews, and table checks.",
        "pages/1_Data_Explorer.py",
    ),
    (
        "User Editor",
        "Edit source records, submit changes as ETL jobs, and undo the latest submitted edit job.",
        "pages/2_User_Editor.py",
    ),
    (
        "Dashboard",
        "Analyze census, capacity pressure, funded capacity gaps, and service planning opportunities.",
        "pages/3_Dashboard.py",
    ),
    (
        "Patient Journey",
        "Trace one encounter through admission, location, service, diagnosis, and discharge events.",
        "pages/4_Patient_Journey.py",
    ),
]

for column, (title, description, page_path) in zip(page_cols, pages):
    with column:
        st.markdown(
            (
                '<div class="page-card">'
                f'<div class="page-title">{title}</div>'
                f'<div class="page-copy">{description}</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )
        st.page_link(page_path, label=f"Open {title}", use_container_width=True)
