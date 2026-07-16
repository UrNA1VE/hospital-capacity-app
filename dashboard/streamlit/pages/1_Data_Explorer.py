"""Explore raw, ETL-prepared, and dashboard mart tables."""

from __future__ import annotations

import streamlit as st

import bootstrap  # noqa: F401
from utils.database import PROJECT_ROOT, RAW_DATA_DIR
from utils.data_explorer import (
    LAYERS,
    RAW_TABLES,
    job_history_preview,
    latest_value,
    layer_summary,
    matching_pipeline_checks,
    quality_checks,
    read_table,
    table_path,
)


st.set_page_config(page_title="Data Explorer", layout="wide")

st.markdown(
    """
    <style>
    .layer-card {
        min-height: 116px;
        border: 1px solid rgba(250, 250, 250, 0.14);
        border-radius: 8px;
        padding: 0.8rem 0.9rem;
        background: rgba(255, 255, 255, 0.03);
        margin-bottom: 0.55rem;
    }
    .layer-card.selected {
        border-color: rgba(255, 75, 75, 0.78);
        background: rgba(255, 75, 75, 0.08);
    }
    .layer-label {
        color: rgba(250, 250, 250, 0.55);
        font-size: 0.74rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
    }
    .layer-title {
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 0.45rem;
    }
    .layer-meta {
        color: rgba(250, 250, 250, 0.68);
        font-size: 0.84rem;
        line-height: 1.35;
    }
    .table-strip {
        border: 1px solid rgba(250, 250, 250, 0.12);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.025);
        padding: 0.7rem 0.85rem;
        margin: 0.8rem 0 1rem;
    }
    .meta-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.6rem;
        margin-bottom: 0.55rem;
    }
    .meta-chip {
        border: 1px solid rgba(250, 250, 250, 0.1);
        border-radius: 6px;
        padding: 0.45rem 0.55rem;
        background: rgba(255, 255, 255, 0.025);
    }
    .meta-label {
        color: rgba(250, 250, 250, 0.52);
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .meta-value {
        color: rgba(250, 250, 250, 0.9);
        font-size: 0.88rem;
        margin-top: 0.15rem;
        overflow-wrap: anywhere;
    }
    .table-description {
        color: rgba(250, 250, 250, 0.68);
        font-size: 0.86rem;
        line-height: 1.38;
    }
    @media (max-width: 900px) {
        .meta-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Data Explorer")
st.caption("Inspect each ETL layer, table grain, freshness, sample rows, and table-level checks.")

if "data_explorer_layer" not in st.session_state:
    st.session_state["data_explorer_layer"] = next(iter(LAYERS))

st.markdown("#### ETL Layer")
layer_cols = st.columns(len(LAYERS))
for column, (layer_name, (layer_folder, layer_tables)) in zip(layer_cols, LAYERS.items()):
    existing_count, total_rows = layer_summary(layer_folder, layer_tables)
    is_selected = layer_name == st.session_state["data_explorer_layer"]
    with column:
        selected_class = " selected" if is_selected else ""
        st.markdown(
            (
                f'<div class="layer-card{selected_class}">'
                f'<div class="layer-label">{"Selected" if is_selected else "Layer"}</div>'
                f'<div class="layer-title">{layer_name}</div>'
                f'<div class="layer-meta">{existing_count}/{len(layer_tables)} tables available<br>{total_rows:,} rows</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )
        if st.button(
            "Selected" if is_selected else "Open layer",
            key=f"data-explorer-layer-{layer_name}",
            disabled=is_selected,
            use_container_width=True,
        ):
            st.session_state["data_explorer_layer"] = layer_name
            st.rerun()

layer = st.session_state["data_explorer_layer"]
folder, tables = LAYERS[layer]

st.markdown("#### Table")
table_name = st.selectbox("Choose one table", list(tables))
meta = tables[table_name]
path = table_path(folder, meta)
frame = read_table(path)

if not path.exists():
    if layer == "Job History":
        st.warning(f"{path.relative_to(PROJECT_ROOT)} does not exist yet. Run a job to create history.")
    else:
        st.warning(f"{path.relative_to(PROJECT_ROOT)} does not exist yet. Initialize the demo dataset first.")
    st.stop()

st.markdown(
    f"""
    <div class="table-strip">
      <div class="meta-grid">
        <div class="meta-chip"><div class="meta-label">Rows</div><div class="meta-value">{len(frame):,}</div></div>
        <div class="meta-chip"><div class="meta-label">Columns</div><div class="meta-value">{len(frame.columns):,}</div></div>
        <div class="meta-chip"><div class="meta-label">Freshness</div><div class="meta-value">{latest_value(frame, meta.freshness_column)}</div></div>
        <div class="meta-chip"><div class="meta-label">Primary key</div><div class="meta-value">{meta.primary_key or "n/a"}</div></div>
        <div class="meta-chip"><div class="meta-label">Layer</div><div class="meta-value">{meta.layer}</div></div>
      </div>
      <div class="table-description"><strong>Grain:</strong> {meta.grain}</div>
      <div class="table-description">{meta.description}</div>
      <div class="table-description">{path.relative_to(PROJECT_ROOT)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("First 5 Rows")
if layer == "Job History":
    st.dataframe(job_history_preview(frame), use_container_width=True, hide_index=True)
else:
    st.dataframe(frame.head(5), use_container_width=True, hide_index=True)

st.subheader("Table Quality Checks")
checks = quality_checks(frame, meta, RAW_TABLES, RAW_DATA_DIR)
styled_checks = checks.style.apply(
    lambda row: [
        "color: #5be28c; font-weight: 700" if row["status"] == "pass" and column == "status"
        else "color: #ff6b6b; font-weight: 700" if row["status"] == "fail" and column == "status"
        else ""
        for column in row.index
    ],
    axis=1,
)
st.dataframe(styled_checks, use_container_width=True, hide_index=True)

if layer != "Job History":
    st.subheader("Related Report")
    pipeline_checks = matching_pipeline_checks(table_name)
    if pipeline_checks.empty:
        st.info("No related rows found in the latest pipeline quality report.")
    else:
        st.dataframe(pipeline_checks, use_container_width=True, hide_index=True)
