"""Load prepared data used by dashboard and patient journey pages."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from etl.pipeline.paths import DASHBOARD_PREPARED_DIR, ETL_PREPARED_DIR, RAW_DATA_DIR


@st.cache_data
def read_dashboard_marts() -> dict[str, pd.DataFrame]:
    required_files = [
        DASHBOARD_PREPARED_DIR / "daily.csv",
        DASHBOARD_PREPARED_DIR / "pressure.csv",
        DASHBOARD_PREPARED_DIR / "current_demand.csv",
        DASHBOARD_PREPARED_DIR / "projection.csv",
        DASHBOARD_PREPARED_DIR / "facility_filters.csv",
    ]
    if not all(path.exists() for path in required_files):
        raise FileNotFoundError("Dashboard mart data is missing.")

    return {
        "daily": pd.read_csv(DASHBOARD_PREPARED_DIR / "daily.csv", parse_dates=["calendar_date"]),
        "pressure": pd.read_csv(DASHBOARD_PREPARED_DIR / "pressure.csv", parse_dates=["calendar_date"]),
        "current_demand": pd.read_csv(DASHBOARD_PREPARED_DIR / "current_demand.csv"),
        "projection": pd.read_csv(DASHBOARD_PREPARED_DIR / "projection.csv"),
        "facility_filters": pd.read_csv(DASHBOARD_PREPARED_DIR / "facility_filters.csv"),
    }


@st.cache_data
def read_patient_journey_data() -> dict[str, pd.DataFrame]:
    required_files = [
        ETL_PREPARED_DIR / "visits.csv",
        ETL_PREPARED_DIR / "unit_changes.csv",
        RAW_DATA_DIR / "facilities.csv",
        RAW_DATA_DIR / "services.csv",
        RAW_DATA_DIR / "units.csv",
        RAW_DATA_DIR / "diagnoses.csv",
        RAW_DATA_DIR / "admission_chart.csv",
        RAW_DATA_DIR / "patient_events.csv",
    ]
    if not all(path.exists() for path in required_files):
        raise FileNotFoundError("Prepared patient journey data is missing.")

    return {
        "visits": pd.read_csv(ETL_PREPARED_DIR / "visits.csv", parse_dates=["admission_ts", "discharge_ts"]),
        "unit_changes": pd.read_csv(ETL_PREPARED_DIR / "unit_changes.csv", parse_dates=["event_ts"]),
        "admission_chart": pd.read_csv(RAW_DATA_DIR / "admission_chart.csv", parse_dates=["admission_ts"]),
        "patient_events": pd.read_csv(RAW_DATA_DIR / "patient_events.csv", parse_dates=["event_ts"]),
        "facilities": pd.read_csv(RAW_DATA_DIR / "facilities.csv"),
        "services": pd.read_csv(RAW_DATA_DIR / "services.csv"),
        "units": pd.read_csv(RAW_DATA_DIR / "units.csv"),
        "diagnoses": pd.read_csv(RAW_DATA_DIR / "diagnoses.csv"),
    }


@st.cache_data
def read_analysis_tables() -> dict[str, pd.DataFrame]:
    required_files = [
        DASHBOARD_PREPARED_DIR / "daily.csv",
        ETL_PREPARED_DIR / "visits.csv",
        ETL_PREPARED_DIR / "unit_changes.csv",
        RAW_DATA_DIR / "facilities.csv",
        RAW_DATA_DIR / "services.csv",
        RAW_DATA_DIR / "units.csv",
        RAW_DATA_DIR / "diagnoses.csv",
        RAW_DATA_DIR / "population_growth.csv",
    ]
    if not all(path.exists() for path in required_files):
        raise FileNotFoundError("Prepared analysis data is missing.")

    return {
        "daily": pd.read_csv(DASHBOARD_PREPARED_DIR / "daily.csv", parse_dates=["calendar_date"]),
        "visits": pd.read_csv(ETL_PREPARED_DIR / "visits.csv", parse_dates=["admission_ts", "discharge_ts"]),
        "unit_changes": pd.read_csv(ETL_PREPARED_DIR / "unit_changes.csv", parse_dates=["event_ts"]),
        "facilities": pd.read_csv(RAW_DATA_DIR / "facilities.csv"),
        "services": pd.read_csv(RAW_DATA_DIR / "services.csv"),
        "units": pd.read_csv(RAW_DATA_DIR / "units.csv"),
        "diagnoses": pd.read_csv(RAW_DATA_DIR / "diagnoses.csv"),
        "population_growth": pd.read_csv(RAW_DATA_DIR / "population_growth.csv"),
    }
