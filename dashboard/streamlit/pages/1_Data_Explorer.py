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
        with st.container(border=True):
            st.markdown(f"**{layer_name}**")
            st.caption("Selected layer" if is_selected else f"{existing_count}/{len(layer_tables)} tables available")
            st.metric("Rows", f"{total_rows:,}")
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

with st.container(border=True):
    info_cols = st.columns([1, 1, 1.2, 1.2, 1.4])
    info_cols[0].caption(f"Rows: {len(frame):,}")
    info_cols[1].caption(f"Columns: {len(frame.columns):,}")
    info_cols[2].caption(f"Freshness: {latest_value(frame, meta.freshness_column)}")
    info_cols[3].caption(f"Primary key: {meta.primary_key or 'n/a'}")
    info_cols[4].caption(f"Layer: {meta.layer}")
    st.caption(f"Grain: {meta.grain}")
    st.caption(meta.description)
    st.caption(str(path.relative_to(PROJECT_ROOT)))

st.subheader("First 5 Rows")
if layer == "Job History":
    st.dataframe(job_history_preview(frame), use_container_width=True, hide_index=True)
else:
    st.dataframe(frame.head(5), use_container_width=True, hide_index=True)

st.subheader("Table Quality Checks")
checks = quality_checks(frame, meta, RAW_TABLES, RAW_DATA_DIR)
st.dataframe(checks, use_container_width=True, hide_index=True)

if layer != "Job History":
    st.subheader("Related Report")
    pipeline_checks = matching_pipeline_checks(table_name)
    if pipeline_checks.empty:
        st.info("No related rows found in the latest pipeline quality report.")
    else:
        st.dataframe(pipeline_checks, use_container_width=True, hide_index=True)
