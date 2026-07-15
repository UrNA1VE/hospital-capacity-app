"""Capacity dashboard for census, pressure, and bed projection."""

from importlib import reload

import pandas as pd
import streamlit as st

import bootstrap  # noqa: F401
from analytics.demographics import demographics_summary
from analytics.projection import bed_needs_projection
from analytics.utilization import current_bed_demand
import utils.charts as charts
from utils.database import load_dashboard_data

charts = reload(charts)

st.set_page_config(page_title="Dashboard", layout="wide")
tables, source_label = load_dashboard_data()

daily = tables["daily"]
visits = tables["visits"]
services = tables["services"]
facilities = tables["facilities"]
diagnoses = tables["diagnoses"]
population_growth = tables["population_growth"]

st.title("Dashboard")
st.caption(f"Capacity analytics from dashboard-ready mart tables. Source: {source_label}")

with st.container(border=True):
    facility = st.selectbox("Facility", ["All"] + sorted(daily["facility_name"].dropna().unique().tolist()))
    service_options = sorted(daily["service_name"].dropna().unique().tolist())
    selected_services = st.multiselect("Services", service_options, default=service_options)

filtered_daily = daily[daily["service_name"].isin(selected_services)]
if facility != "All":
    filtered_daily = filtered_daily[filtered_daily["facility_name"] == facility]

if filtered_daily.empty:
    st.warning("Select at least one service with available rows for this facility.")
    st.stop()

facility_ids = filtered_daily["facility_id"].unique()
service_ids = filtered_daily["service_id"].unique()
filtered_visits = visits[
    visits["facility_id"].isin(facility_ids)
    & visits["service_id"].isin(service_ids)
]

st.subheader("Daily Census & Capacity")
st.altair_chart(charts.daily_census_capacity_chart(filtered_daily), use_container_width=True)

st.subheader("Capacity Pressure")
st.altair_chart(charts.capacity_pressure_chart(filtered_daily), use_container_width=True)

st.subheader("Bed Projection")
current_demand = current_bed_demand(filtered_daily)
demographics = demographics_summary(
    filtered_visits,
    services,
    facilities,
    diagnoses,
)
projection = bed_needs_projection(
    current_demand,
    savings=pd.DataFrame(columns=["facility_name", "service_name", "demand_reduction"]),
    start_year=int(filtered_daily["calendar_date"].dt.year.min()),
    demographics=demographics,
    population_growth=population_growth,
)

demand_col, projection_col = st.columns(2)
with demand_col:
    st.caption("Demand vs Funded Capacity")
    st.altair_chart(charts.bed_demandvsfunded_chart(current_demand), use_container_width=True)

with projection_col:
    st.caption("Projected Bed Need")
    st.altair_chart(charts.bed_needs_projection_chart(projection), use_container_width=True)
