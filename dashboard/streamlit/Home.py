"""ETL control center for the hospital capacity analytics app."""

from pathlib import Path

import streamlit as st

import bootstrap  # noqa: F401
from etl.pipeline.incremental_run import IncrementalDataError, etl_incremental
from etl.pipeline.initialize_dataset import clear_runtime_data, initialize_dataset
from etl.pipeline.paths import PROJECT_ROOT
from etl.pipeline.runtime_state import runtime_summary
from utils.job_logs import render_page_header


st.set_page_config(page_title="Hospital Capacity ETL and Analytics App", page_icon="🏥", layout="wide")

render_page_header(
    "Hospital Capacity ETL and Analytics App",
    "Synthetic event-level healthcare data pipeline with incremental ETL, data quality checks, "
    "editable source records, and dashboard-ready analytics.",
)

st.markdown(
    """
    <style>
    .hero-panel {
        border: 1px solid rgba(250, 250, 250, 0.12);
        border-radius: 8px;
        padding: 1rem 1.1rem;
        background: linear-gradient(135deg, rgba(255, 75, 75, 0.08), rgba(255, 255, 255, 0.025));
        margin-bottom: 1rem;
    }
    .hero-kicker {
        color: #ff6b6b;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .hero-copy {
        color: rgba(250, 250, 250, 0.72);
        line-height: 1.4;
        max-width: 920px;
    }
    .action-note {
        color: rgba(250, 250, 250, 0.65);
        font-size: 0.86rem;
        line-height: 1.35;
        min-height: 42px;
    }
    .how-to-use {
        border: 1px solid rgba(250, 250, 250, 0.12);
        border-radius: 8px;
        padding: 0.75rem 0.9rem;
        background: rgba(255, 255, 255, 0.035);
        color: rgba(250, 250, 250, 0.86);
        font-size: 1rem;
        font-weight: 650;
        margin-bottom: 1rem;
    }
    .how-to-use span {
        color: #ff6b6b;
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
    .page-index {
        color: #ff6b6b;
        font-size: 0.76rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

summary = runtime_summary()
if not summary.data_exists:
    st.warning("Dataset is missing. Click Initialize Dataset to generate the initial 10-day dataset.")
elif summary.data_dirty:
    st.warning("Raw source data is newer than prepared outputs. Submit updates or initialize the dataset to refresh the marts.")

st.markdown(
    '<div class="how-to-use"><span>How to use:</span> Explore seed data -> Run incremental ETL -> '
    "Edit or undo records -> Clear runtime.</div>",
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.subheader("Dataset Actions")
    seed = st.number_input("Select Seed", min_value=1, max_value=999999, value=42, step=1)
    initialize_col, incremental_col, reset_col = st.columns(3)

    with initialize_col:
        if st.button("Initialize Dataset", type="primary", width="stretch"):
            with st.spinner("Generating raw data, validating sources, and building dashboard marts..."):
                result = initialize_dataset(seed=int(seed))
                st.cache_data.clear()
            st.success(
                f"Pipeline complete: {result.validation_status.upper()} "
                f"({result.validation_issue_count} blocking validation issues)."
            )
            st.caption(f"Raw: {Path(result.raw_dir).relative_to(PROJECT_ROOT)}")
            st.caption(f"Prepared: {Path(result.prepared_dir).relative_to(PROJECT_ROOT)}")
        st.markdown(
            '<div class="action-note">Create the initial 10-day synthetic dataset and rebuild every downstream table.</div>',
            unsafe_allow_html=True,
        )
    with incremental_col:
        if st.button("Incremental Run", width="stretch"):
            with st.spinner("Appending next-day data and rebuilding dashboard marts..."):
                try:
                    log = etl_incremental(seed=int(seed), length=1)
                except (FileNotFoundError, IncrementalDataError, KeyError) as error:
                    st.error(f"Incremental run failed: {error}")
                else:
                    st.cache_data.clear()
                    st.success("Incremental run complete.")
                    st.code(log, language="json")
        st.markdown(
            '<div class="action-note">Append the next simulated day and refresh ETL/dashboard outputs.</div>',
            unsafe_allow_html=True,
        )

    with reset_col:
        if st.button("Clear Runtime", width="stretch"):
            with st.spinner("Clearing generated runtime data and job history..."):
                clear_runtime_data()
                st.cache_data.clear()
            st.success("Runtime data cleared. Run Initialize Dataset to create fresh data.")
        st.markdown(
            '<div class="action-note">Clear generated data, prepared outputs, reports, and job history.</div>',
            unsafe_allow_html=True,
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

for page_index, (column, (title, description, page_path)) in enumerate(zip(page_cols, pages), start=1):
    with column:
        st.markdown(
            (
                '<div class="page-card">'
                f'<div class="page-index">PAGE {page_index}</div>'
                f'<div class="page-title">{title}</div>'
                f'<div class="page-copy">{description}</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )
        st.page_link(page_path, label=f"Open {title}", width="stretch")


st.subheader("Pipeline Workflow")
st.caption("The workflow scales to show the full end-to-end pipeline at a glance.")
st.html(
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
    """
)
