"""ETL control center for the hospital capacity analytics app."""

from pathlib import Path

import streamlit as st

import bootstrap  # noqa: F401
from etl.pipeline.incremental_run import IncrementalDataError, etl_incremental
from etl.pipeline.initialize_dataset import clear_runtime_data, initialize_dataset
from config.paths import PROJECT_ROOT
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
    :root {
        --hc-accent: #ff6b6b;
        --hc-blue: #6fc7ff;
        --hc-border: rgba(250, 250, 250, 0.16);
        --hc-muted: rgba(250, 250, 250, 0.72);
        --hc-soft: rgba(255, 255, 255, 0.035);
        --hc-accent-soft: rgba(255, 107, 107, 0.08);
        --hc-blue-soft: rgba(111, 199, 255, 0.08);
    }
    .hero-panel {
        border: 1px solid var(--hc-border);
        border-radius: 8px;
        padding: 1rem 1.1rem;
        background: linear-gradient(135deg, var(--hc-accent-soft), var(--hc-soft));
        margin-bottom: 1rem;
    }
    .hero-kicker {
        color: var(--hc-accent);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .hero-copy {
        color: var(--hc-muted);
        line-height: 1.4;
        max-width: 920px;
    }
    .action-note {
        color: var(--hc-muted);
        font-size: 0.86rem;
        line-height: 1.35;
        min-height: 42px;
    }
    .how-to-use {
        border: 1px solid var(--hc-border);
        border-radius: 8px;
        padding: 0.75rem 0.9rem;
        background: var(--hc-soft);
        color: var(--text-color);
        font-size: 1rem;
        font-weight: 650;
        margin-bottom: 1rem;
    }
    .how-to-use span {
        color: var(--hc-accent);
    }
    .page-card {
        min-height: 158px;
        border: 1px solid var(--hc-border);
        border-radius: 8px;
        padding: 0.95rem;
        background: var(--hc-soft);
        margin-bottom: 0.7rem;
    }
    .page-title {
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .page-copy {
        color: var(--hc-muted);
        font-size: 0.9rem;
        line-height: 1.35;
    }
    .page-index {
        color: var(--hc-accent);
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
st.caption("User edits feed back into the raw source layer, then validation and downstream marts are rebuilt.")
st.html(
    """
    <style>
      body {
        margin: 0;
        background: transparent;
        color: #f5f5f5;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      :root {
        --hc-accent: #ff6b6b;
        --hc-blue: #6fc7ff;
        --hc-border: rgba(250, 250, 250, 0.18);
        --hc-line: rgba(250, 250, 250, 0.68);
        --hc-muted: rgba(250, 250, 250, 0.72);
        --hc-soft: rgba(255, 255, 255, 0.04);
        --hc-accent-soft: rgba(255, 107, 107, 0.08);
        --hc-blue-soft: rgba(111, 199, 255, 0.08);
      }
      .pipeline-map {
        width: 100%;
      }
      .pipeline-canvas {
        position: relative;
        width: 100%;
        aspect-ratio: 1190 / 300;
        min-height: 230px;
        border: 1px solid var(--hc-border);
        border-radius: 8px;
        background: var(--hc-soft);
      }
      .pipeline-node {
        position: absolute;
        width: 13.8%;
        min-height: 54px;
        border: 1px solid var(--hc-border);
        border-radius: 6px;
        padding: 0.55rem 0.65rem;
        background: var(--background-color, transparent);
        text-align: center;
        box-sizing: border-box;
      }
      .pipeline-node.source {
        border-color: var(--hc-accent);
        background: var(--hc-accent-soft);
      }
      .pipeline-node.editor {
        width: 13.8%;
        border-color: var(--hc-blue);
        background: var(--hc-blue-soft);
      }
      .pipeline-title {
        font-weight: 700;
        font-size: clamp(0.58rem, 1.05vw, 0.86rem);
        line-height: 1.2;
      }
      .pipeline-copy {
        color: var(--hc-muted);
        font-size: clamp(0.52rem, 0.9vw, 0.8rem);
        line-height: 1.35;
        margin-top: 0.25rem;
      }
      .pipeline-arrow {
        position: absolute;
        color: var(--hc-line);
        font-size: clamp(1.1rem, 2vw, 1.45rem);
        font-weight: 700;
        line-height: 1;
        transform: translate(-50%, -50%);
      }
      .pipeline-arrow.editor-flow {
        color: var(--hc-blue);
      }
    </style>
    <div class="pipeline-map">
        <div class="pipeline-canvas">
            <div class="pipeline-arrow" style="left: 17%; top: 55%;">→</div>
            <div class="pipeline-arrow" style="left: 33%; top: 55%;">→</div>
            <div class="pipeline-arrow" style="left: 49%; top: 55%;">→</div>
            <div class="pipeline-arrow" style="left: 65%; top: 55%;">→</div>
            <div class="pipeline-arrow" style="left: 81%; top: 55%;">→</div>
            <div class="pipeline-arrow editor-flow" style="left: 24.9%; top: 37%;">↓</div>
            <div class="pipeline-node" style="left: 2%; top: 42%;">
                <div class="pipeline-title">Run Control</div>
                <div class="pipeline-copy">initialize +<br>incremental run</div>
            </div>
            <div class="pipeline-node editor" style="left: 18%; top: 10%;">
                <div class="pipeline-title">User Editor</div>
                <div class="pipeline-copy">edit events +<br>undo latest edit</div>
            </div>
            <div class="pipeline-node source" style="left: 18%; top: 42%;">
                <div class="pipeline-title">Synthetic Raw Sources</div>
                <div class="pipeline-copy">patients, admissions,<br>events, capacity</div>
            </div>
            <div class="pipeline-node" style="left: 34%; top: 42%;">
                <div class="pipeline-title">Data Quality Checks</div>
                <div class="pipeline-copy">schema, keys,<br>ranges, references</div>
            </div>
            <div class="pipeline-node" style="left: 50%; top: 42%;">
                <div class="pipeline-title">ETL Prepared Layer</div>
                <div class="pipeline-copy">visits +<br>unit_changes</div>
            </div>
            <div class="pipeline-node" style="left: 66%; top: 42%;">
                <div class="pipeline-title">Dashboard Marts</div>
                <div class="pipeline-copy">daily, census, pressure,<br>demand, projection</div>
            </div>
            <div class="pipeline-node" style="left: 82%; top: 42%;">
                <div class="pipeline-title">Analytics App</div>
                <div class="pipeline-copy">explore data,<br>edit, dashboard</div>
            </div>
        </div>
    </div>
    """
)
