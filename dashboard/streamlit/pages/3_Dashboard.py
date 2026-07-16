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

st.markdown(
    """
    <style>
    .dashboard-note {
        color: rgba(250, 250, 250, 0.68);
        font-size: 0.88rem;
        line-height: 1.38;
    }
    .kpi-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.85rem 0 1.1rem;
    }
    .kpi-card {
        border: 1px solid rgba(250, 250, 250, 0.12);
        border-radius: 8px;
        padding: 0.75rem 0.85rem;
        background: rgba(255, 255, 255, 0.03);
    }
    .kpi-label {
        color: rgba(250, 250, 250, 0.55);
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .kpi-value {
        color: rgba(250, 250, 250, 0.95);
        font-size: 1.35rem;
        font-weight: 760;
        margin-top: 0.25rem;
    }
    .section-caption {
        color: rgba(250, 250, 250, 0.62);
        font-size: 0.86rem;
        margin-top: -0.25rem;
        margin-bottom: 0.45rem;
    }
    @media (max-width: 900px) {
        .kpi-strip {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

daily = tables["daily"]
visits = tables["visits"]
services = tables["services"]
facilities = tables["facilities"]
diagnoses = tables["diagnoses"]
population_growth = tables["population_growth"]

st.title("Dashboard")
st.caption(f"Capacity analytics from dashboard-ready mart tables. Source: {source_label}")

with st.container(border=True):
    st.markdown("**Filters**")
    st.markdown(
        '<div class="dashboard-note">Scope the marts by facility and clinical service before reviewing census, pressure, and projected demand.</div>',
        unsafe_allow_html=True,
    )
    facility_col, service_col = st.columns([1, 2])
    with facility_col:
        facility = st.selectbox("Facility", ["All"] + sorted(daily["facility_name"].dropna().unique().tolist()))
    with service_col:
        service_options = sorted(daily["service_name"].dropna().unique().tolist())
        selected_services = st.multiselect("Services", service_options, default=service_options)

filtered_daily = daily[daily["service_name"].isin(selected_services)]
if facility != "All":
    filtered_daily = filtered_daily[filtered_daily["facility_name"] == facility]

if filtered_daily.empty:
    st.warning("Select at least one service with available rows for this facility.")
    st.stop()

latest_date = filtered_daily["calendar_date"].max().date().isoformat()
total_peak_census = int(filtered_daily.groupby("calendar_date")["peak_census"].sum().max())
total_staffed_beds = int(filtered_daily.groupby("calendar_date")["staffed_beds"].sum().max())
avg_utilization = filtered_daily["peak_utilization"].mean()

st.markdown(
    f"""
    <div class="kpi-strip">
      <div class="kpi-card"><div class="kpi-label">Latest date</div><div class="kpi-value">{latest_date}</div></div>
      <div class="kpi-card"><div class="kpi-label">Peak census</div><div class="kpi-value">{total_peak_census:,}</div></div>
      <div class="kpi-card"><div class="kpi-label">Staffed beds</div><div class="kpi-value">{total_staffed_beds:,}</div></div>
      <div class="kpi-card"><div class="kpi-label">Avg utilization</div><div class="kpi-value">{avg_utilization:.0%}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

facility_ids = filtered_daily["facility_id"].unique()
service_ids = filtered_daily["service_id"].unique()
filtered_visits = visits[
    visits["facility_id"].isin(facility_ids)
    & visits["service_id"].isin(service_ids)
]

st.subheader("Daily Census & Capacity")
st.markdown('<div class="section-caption">Peak daily census by service compared with available staffed capacity.</div>', unsafe_allow_html=True)
st.altair_chart(charts.daily_census_capacity_chart(filtered_daily), use_container_width=True)

st.subheader("Capacity Pressure")
st.markdown('<div class="section-caption">Utilization pressure over time after applying the selected facility and service filters.</div>', unsafe_allow_html=True)
st.altair_chart(charts.capacity_pressure_chart(filtered_daily), use_container_width=True)

st.subheader("Bed Projection")
st.markdown('<div class="section-caption">Current demand and projected bed need using the prepared dashboard marts.</div>', unsafe_allow_html=True)
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
