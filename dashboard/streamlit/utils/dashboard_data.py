"""Load prepared data used by dashboard and patient journey pages."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.paths import (
    ANALYSIS_REQUIRED_PATHS,
    DASHBOARD_MART_REQUIRED_PATHS,
    DASHBOARD_TABLE_PATHS,
    ETL_PREPARED_TABLE_PATHS,
    PATIENT_JOURNEY_REQUIRED_PATHS,
    RAW_TABLE_PATHS,
)


@st.cache_data
def read_dashboard_marts() -> dict[str, pd.DataFrame]:
    if not all(path.exists() for path in DASHBOARD_MART_REQUIRED_PATHS):
        raise FileNotFoundError("Dashboard mart data is missing.")

    return {
        "daily": pd.read_csv(DASHBOARD_TABLE_PATHS["daily"], parse_dates=["calendar_date"]),
        "pressure": pd.read_csv(DASHBOARD_TABLE_PATHS["pressure"], parse_dates=["calendar_date"]),
        "current_demand": pd.read_csv(DASHBOARD_TABLE_PATHS["current_demand"]),
        "projection": pd.read_csv(DASHBOARD_TABLE_PATHS["projection"]),
        "facility_filters": pd.read_csv(DASHBOARD_TABLE_PATHS["facility_filters"]),
    }


@st.cache_data
def read_patient_journey_data() -> dict[str, pd.DataFrame]:
    if not all(path.exists() for path in PATIENT_JOURNEY_REQUIRED_PATHS):
        raise FileNotFoundError("Prepared patient journey data is missing.")

    return {
        "visits": pd.read_csv(ETL_PREPARED_TABLE_PATHS["visits"], parse_dates=["admission_ts", "discharge_ts"]),
        "unit_changes": pd.read_csv(ETL_PREPARED_TABLE_PATHS["unit_changes"], parse_dates=["event_ts"]),
        "admission_chart": pd.read_csv(RAW_TABLE_PATHS["admission_chart"], parse_dates=["admission_ts"]),
        "patient_events": pd.read_csv(RAW_TABLE_PATHS["patient_events"], parse_dates=["event_ts"]),
        "facilities": pd.read_csv(RAW_TABLE_PATHS["facilities"]),
        "services": pd.read_csv(RAW_TABLE_PATHS["services"]),
        "units": pd.read_csv(RAW_TABLE_PATHS["units"]),
        "diagnoses": pd.read_csv(RAW_TABLE_PATHS["diagnoses"]),
    }


@st.cache_data
def read_analysis_tables() -> dict[str, pd.DataFrame]:
    if not all(path.exists() for path in ANALYSIS_REQUIRED_PATHS):
        raise FileNotFoundError("Prepared analysis data is missing.")

    return {
        "daily": pd.read_csv(DASHBOARD_TABLE_PATHS["daily"], parse_dates=["calendar_date"]),
        "visits": pd.read_csv(ETL_PREPARED_TABLE_PATHS["visits"], parse_dates=["admission_ts", "discharge_ts"]),
        "unit_changes": pd.read_csv(ETL_PREPARED_TABLE_PATHS["unit_changes"], parse_dates=["event_ts"]),
        "facilities": pd.read_csv(RAW_TABLE_PATHS["facilities"]),
        "services": pd.read_csv(RAW_TABLE_PATHS["services"]),
        "units": pd.read_csv(RAW_TABLE_PATHS["units"]),
        "diagnoses": pd.read_csv(RAW_TABLE_PATHS["diagnoses"]),
        "population_growth": pd.read_csv(RAW_TABLE_PATHS["population_growth"]),
    }
