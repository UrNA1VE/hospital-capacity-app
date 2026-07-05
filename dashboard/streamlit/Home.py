"""Pipeline landing page for the hospital capacity data demo."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

import bootstrap  # noqa: F401
from etl.pipeline.incremental_run import IncrementalDataError, etl_incremental
from etl.pipeline.initialize_demo_dataset import RAW_DATA_DIR, REPORT_DATA_DIR, run_fake_data_pipeline


st.set_page_config(page_title="Healthcare Capacity Pipeline", page_icon="🏥", layout="wide")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DATA_DIR = PROJECT_ROOT / "data" / "dashboard_prepared"
EVENT_SOURCE_FILES = {"patients.csv", "admission_chart.csv", "patient_events.csv"}
REFERENCE_SOURCE_FILES = {
    "capacity.csv",
    "diagnoses.csv",
    "facilities.csv",
    "population_growth.csv",
    "services.csv",
    "units.csv",
}
AGGREGATED_SOURCE_FILES = {
    "capacity.csv",
    "census.csv",
    "current_demand.csv",
    "daily.csv",
    "demand.csv",
    "demographics.csv",
    "pressure.csv",
    "projection.csv",
    "quality.csv",
    "savings.csv",
}
ETL_PREPARED_DATA_DIR = PROJECT_ROOT / "data" / "etl_prepared"
RAW_PIPELINE_FILES = {
    "patients.csv": ("patient_id", ("registration_date",)),
    "admission_chart.csv": ("visit_id", ("admission_ts",)),
    "patient_events.csv": ("event_id", ("event_ts",)),
    "capacity.csv": ("capacity_date", ("capacity_date",)),
}
ETL_PIPELINE_FILES = {
    "visits.csv": ("visit_id", ("admission_ts", "discharge_ts")),
}
DASHBOARD_PIPELINE_FILES = {
    "daily.csv": ("calendar_date", ("calendar_date",)),
    "census.csv": ("hour_ts", ("hour_ts",)),
    "pressure.csv": ("calendar_date", ("calendar_date",)),
    "quality.csv": ("check_name", ()),
}


@st.cache_data
def read_csv_preview(path: str, modified_ns: int) -> pd.DataFrame:
    return pd.read_csv(path).head(100)


def format_date(value: object) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    return timestamp.date().isoformat() if pd.notna(timestamp) else "n/a"


@st.cache_data
def read_csv_profile(path: str, freshness_columns: tuple[str, ...], modified_ns: int) -> dict[str, object]:
    frame = pd.read_csv(path)
    latest_values = []
    for column in freshness_columns:
        if column in frame.columns:
            values = pd.to_datetime(frame[column], errors="coerce")
            if values.notna().any():
                latest_values.append(values.max())

    latest = max(latest_values) if latest_values else pd.NaT
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "latest": format_date(latest),
    }


def list_csvs(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.csv")) if folder.exists() else []


def profile_csvs(folder: Path, file_config: dict[str, tuple[str, tuple[str, ...]]]) -> pd.DataFrame:
    rows = []
    for file_name, (_, freshness_columns) in file_config.items():
        path = folder / file_name
        if not path.exists():
            rows.append(
                {
                    "table": file_name.removesuffix(".csv"),
                    "rows": "missing",
                    "columns": "missing",
                    "freshness": "missing",
                }
            )
            continue
        profile = read_csv_profile(str(path), freshness_columns, path.stat().st_mtime_ns)
        rows.append(
            {
                "table": file_name.removesuffix(".csv"),
                "rows": profile["rows"],
                "columns": profile["columns"],
                "freshness": profile["latest"],
            }
        )
    return pd.DataFrame(rows)


def dashboard_mart_end_date() -> str:
    daily_path = PREPARED_DATA_DIR / "daily.csv"
    if daily_path.exists():
        daily_profile = read_csv_profile(str(daily_path), ("calendar_date",), daily_path.stat().st_mtime_ns)
        if daily_profile["latest"] != "n/a":
            return str(daily_profile["latest"])

    raw_capacity_path = RAW_DATA_DIR / "capacity.csv"
    if raw_capacity_path.exists():
        capacity_profile = read_csv_profile(
            str(raw_capacity_path),
            ("capacity_date",),
            raw_capacity_path.stat().st_mtime_ns,
        )
        return str(capacity_profile["latest"])

    return "n/a"


def profile_dashboard_marts() -> pd.DataFrame:
    end_date = dashboard_mart_end_date()
    profile = profile_csvs(PREPARED_DATA_DIR, {name: (key, ()) for name, (key, _) in DASHBOARD_PIPELINE_FILES.items()})
    profile["freshness"] = end_date
    return profile


def load_quality_summary() -> tuple[pd.DataFrame, str]:
    quality_path = PREPARED_DATA_DIR / "quality.csv"
    report_path = REPORT_DATA_DIR / "data_check_report.csv"
    if quality_path.exists():
        return pd.read_csv(quality_path), str(quality_path.relative_to(PROJECT_ROOT))
    if report_path.exists():
        return pd.read_csv(report_path), str(report_path.relative_to(PROJECT_ROOT))
    return pd.DataFrame(columns=["check_name", "severity", "issue_count", "details", "status"]), "not generated"


def load_incremental_summary() -> dict[str, object] | None:
    path = REPORT_DATA_DIR / "latest_incremental_run.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"status": "unreadable", "path": str(path.relative_to(PROJECT_ROOT))}


def render_pipeline_status() -> None:
    st.subheader("Pipeline Status")
    raw_profile = profile_csvs(RAW_DATA_DIR, RAW_PIPELINE_FILES)
    etl_profile = profile_csvs(ETL_PREPARED_DATA_DIR, ETL_PIPELINE_FILES)
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

    profile_tab, check_tab = st.tabs(["Layer Tables", "Data Checks"])
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


st.title("Healthcare Capacity Analytics Pipeline")
st.caption("Generate synthetic event-level source data, validate it, and build dashboard-ready aggregated tables.")

with st.expander("Data Generator", expanded=True):
    seed = st.number_input("Seed", min_value=1, max_value=999999, value=42, step=1)
    incre_seed = seed
    generate_col, incremental_col = st.columns(2)
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
