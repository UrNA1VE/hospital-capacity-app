from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "dashboard" / "streamlit"))

from analytics.demographics import demographics_summary  # noqa: E402
from analytics.journey import journey_segments, patient_visit_summary  # noqa: E402
from analytics.projection import bed_needs_projection  # noqa: E402
from analytics.utilization import bed_demand_no_adjustment, capacity_summary, current_bed_demand  # noqa: E402
from utils.dashboard_data import read_analysis_tables  # noqa: E402


def analysis_tables():
    return read_analysis_tables()


def test_sanitized_bed_analysis_outputs_are_nonempty():
    tables = analysis_tables()
    daily = tables["daily"]
    visits = tables["visits"]
    services = tables["services"]
    facilities = tables["facilities"]
    diagnoses = tables["diagnoses"]
    population_growth = tables["population_growth"]

    capacity = capacity_summary(daily)
    demographics = demographics_summary(visits, services, facilities, diagnoses)
    demand = bed_demand_no_adjustment(daily, demographics, population_growth)
    current_demand = current_bed_demand(daily)
    projection = bed_needs_projection(
        current_demand,
        start_year=int(daily["calendar_date"].dt.year.min()),
        demographics=demographics,
        population_growth=population_growth,
    )

    assert {"facility_name", "service_name", "planned_beds"} <= set(capacity.columns)
    assert {"year", "demand", "funded_capacity", "variance", "growth_index"} <= set(demand.columns)
    assert {"demand", "funded_capacity", "variance"} <= set(current_demand.columns)
    assert {"gender", "age_group", "region", "patient_days"} <= set(demographics.columns)
    assert {"year", "projection", "adjusted_projection"} <= set(projection.columns)
    assert demand["demand"].gt(0).all()
    assert demand["year"].max() == 2040
    assert projection["year"].max() == 2040
    assert projection["adjusted_projection"].equals(projection["projection"])


def test_patient_journey_segments_include_location_and_service_tracks():
    tables = analysis_tables()
    visit_id = tables["visits"]["visit_id"].iloc[0]

    summary = patient_visit_summary(
        visit_id,
        tables["visits"],
        tables["facilities"],
        tables["services"],
        tables["diagnoses"],
    )
    segments = journey_segments(
        visit_id,
        tables["visits"],
        tables["unit_changes"],
        tables["units"],
        tables["services"],
    )

    assert summary["visit_id"] == visit_id
    assert {"Location", "Service"} <= set(segments["track"])
    assert (segments["end_ts"] > segments["start_ts"]).all()
