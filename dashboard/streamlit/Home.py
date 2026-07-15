"""Pipeline landing page for the hospital capacity data demo."""

from pathlib import Path

import streamlit as st

import bootstrap  # noqa: F401
from etl.pipeline.incremental_run import IncrementalDataError, etl_incremental
from etl.pipeline.initialize_demo_dataset import reset_demo_runtime, run_fake_data_pipeline, RUN_HISTORY_PATH, EDIT_HISTORY_PATH
from utils.database import (
    AGGREGATED_SOURCE_FILES,
    EVENT_SOURCE_FILES,
    PREPARED_DATA_DIR,
    PROJECT_ROOT,
    RAW_DATA_DIR,
    REFERENCE_SOURCE_FILES,
    REPORT_DATA_DIR,
    read_csv_preview,
    read_csv_profile,
)
from utils.report import data_viewer, render_pipeline_status

for path in [RUN_HISTORY_PATH, EDIT_HISTORY_PATH]:
    if path.exists():
        path.unlink()

st.set_page_config(page_title="Hospital Capacity Analytics App", page_icon="🏥", layout="wide")
st.title("Hospital Capacity Analytics App")
st.caption("Generate synthetic event-level source data, validate it, and build dashboard-ready aggregated tables.")

with st.expander("Data Generator", expanded=True):
    seed = st.number_input("Seed", min_value=1, max_value=999999, value=42, step=1)
    incre_seed = seed
    generate_col, incremental_col, reset_col = st.columns(3)
    with generate_col:
        if st.button("Initial First Month Data", type="primary", use_container_width=True):
            with st.spinner("Generating container-local raw data, validating, and transforming..."):
                result = run_fake_data_pipeline(seed=int(seed))
                read_csv_preview.clear()
                read_csv_profile.clear()
                st.success(
                    f"Pipeline complete: {result.validation_status.upper()} "
                    f"({result.validation_issue_count} blocking validation issues)."
                )
                st.caption(f"Raw: {Path(result.raw_dir).relative_to(PROJECT_ROOT)}")
                st.caption(f"Report: {Path(result.report_dir).relative_to(PROJECT_ROOT)}")
                st.caption(f"Aggregated: {Path(result.prepared_dir).relative_to(PROJECT_ROOT)}")
    with incremental_col:
        if st.button("Incremental Run(add next-day data)", use_container_width=True):
            with st.spinner("Appending the next simulated day and rebuilding dashboard outputs..."):
                try:
                    log = etl_incremental(seed=incre_seed, length=1)
                except (FileNotFoundError, IncrementalDataError, KeyError) as error:
                    st.error(f"Incremental run failed: {error}")
                else:
                    read_csv_preview.clear()
                    read_csv_profile.clear()
                    st.success("Incremental run complete.")
                    st.code(log, language="json")
                incre_seed += 1
    with reset_col:
        # confirm_reset = st.checkbox("Confirm reset")
        if st.button("Reset Demo", use_container_width=True):
            reset_demo_runtime()
            read_csv_preview.clear()
            read_csv_profile.clear()
            st.success("Demo runtime cleared. Generate initial data to start a new session.")

render_pipeline_status()

tab_event, tab_reference, tab_aggregated, tab_quality = st.tabs(["Source Data", "Reference Data", "Aggregated Data", "Quality Report"])

with tab_event:
    st.subheader("Source Data")
    data_viewer("Event", RAW_DATA_DIR, EVENT_SOURCE_FILES)


with tab_reference:
    st.subheader("Reference Data")
    data_viewer("Reference", RAW_DATA_DIR, REFERENCE_SOURCE_FILES)

with tab_aggregated:
    st.subheader("Aggregated Data")
    data_viewer("Aggregated", PREPARED_DATA_DIR, AGGREGATED_SOURCE_FILES)

with tab_quality:
    st.subheader("Quality Report")
    data_viewer("Report", REPORT_DATA_DIR)
