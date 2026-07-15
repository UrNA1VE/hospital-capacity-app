"""ETL control center for the hospital capacity analytics app."""

from pathlib import Path

import streamlit as st

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
    .workflow {
        display: flex;
        align-items: stretch;
        gap: 0.55rem;
        margin: 0.25rem 0 1.5rem;
    }
    .workflow-step {
        flex: 1;
        min-height: 118px;
        border: 1px solid rgba(250, 250, 250, 0.14);
        border-radius: 8px;
        padding: 0.85rem;
        background: rgba(255, 255, 255, 0.035);
    }
    .workflow-title {
        font-weight: 700;
        margin-bottom: 0.45rem;
    }
    .workflow-copy {
        color: rgba(250, 250, 250, 0.68);
        font-size: 0.9rem;
        line-height: 1.35;
    }
    .workflow-arrow {
        display: flex;
        align-items: center;
        color: #ff4b4b;
        font-size: 1.7rem;
        font-weight: 700;
    }
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
workflow_steps = [
    (
        "Synthetic Generator",
        "Creates patients, admissions, events, capacity, and reference data.",
    ),
    (
        "Raw Source Layer",
        "patients, admission_chart, patient_events, capacity, reference CSVs.",
    ),
    (
        "Data Quality Checks",
        "Validates schema, keys, date ranges, and reference integrity.",
    ),
    (
        "ETL Prepared Layer",
        "Derives visit-level encounter outputs from the event source of truth.",
    ),
    (
        "Dashboard Marts",
        "Builds daily, census, pressure, demand, savings, projection, and quality tables.",
    ),
]

workflow_html = '<div class="workflow">'
for index, (title, description) in enumerate(workflow_steps):
    workflow_html += (
        '<div class="workflow-step">'
        f'<div class="workflow-title">{title}</div>'
        f'<div class="workflow-copy">{description}</div>'
        '</div>'
    )
    if index < len(workflow_steps) - 1:
        workflow_html += '<div class="workflow-arrow">→</div>'
workflow_html += "</div>"
st.markdown(workflow_html, unsafe_allow_html=True)

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
