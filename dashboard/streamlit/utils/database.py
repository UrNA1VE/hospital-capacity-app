"""Dashboard data access and CSV profiling utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from etl.pipeline.job_logger import RUN_HISTORY_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "synthetic" / "sample_data"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "container" / "raw"
REPORT_DATA_DIR = PROJECT_ROOT / "data" / "container" / "reports"
ETL_PREPARED_DIR = PROJECT_ROOT / "data" / "etl_prepared"
DASHBOARD_PREPARED_DIR = PROJECT_ROOT / "data" / "dashboard_prepared"
PREPARED_DATA_DIR = DASHBOARD_PREPARED_DIR
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
RAW_PIPELINE_FILES = {
    "patients.csv": ("patient_id", ("registration_date",)),
    "admission_chart.csv": ("visit_id", ("admission_ts",)),
    "patient_events.csv": ("event_id", ("event_ts",)),
    "capacity.csv": ("capacity_date", ("capacity_date",)),
}
ETL_PIPELINE_FILES = {
    "visits.csv": ("visit_id", ("admission_ts", "discharge_ts")),
    "unit_changes.csv": ("unit_change_id", ("event_ts",)),
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


def load_run_history() -> pd.DataFrame:
    if not RUN_HISTORY_PATH.exists():
        return pd.DataFrame(
            columns=[
                "job_id",
                "job_type",
                "status",
                "started_at",
                "finished_at",
                "duration_seconds",
                "message",
                "changes",
            ]
        )
    history = pd.read_csv(RUN_HISTORY_PATH)
    return history.sort_values("started_at", ascending=False)


def _hourly_snapshots(
    visits: pd.DataFrame,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for _, row in visits.iterrows():
        admission_ts = pd.Timestamp(row["admission_ts"])
        discharge_ts = pd.Timestamp(row["discharge_ts"])
        if pd.isna(discharge_ts):
            if end is None:
                continue
            discharge_ts = end
        snapshot_start = max(admission_ts, start) if start is not None else admission_ts
        snapshot_end = min(discharge_ts, end) if end is not None else discharge_ts
        first_hour = snapshot_start.ceil("h")
        if first_hour >= snapshot_end:
            continue
        hours = pd.date_range(first_hour, snapshot_end, freq="h", inclusive="left")
        if hours.empty:
            continue
        frames.append(
            pd.DataFrame(
                {
                    "visit_id": row["visit_id"],
                    "facility_id": row["facility_id"],
                    "service_id": row["service_id"],
                    "hour_ts": hours,
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=["visit_id", "facility_id", "service_id", "hour_ts"])
    return pd.concat(frames, ignore_index=True)


def read_sample_sources() -> dict[str, pd.DataFrame]:
    return {
        "visits": pd.read_csv(
            SAMPLE_DATA_DIR / "visits.csv",
            parse_dates=["admission_ts", "discharge_ts"],
        ),
        "facilities": pd.read_csv(SAMPLE_DATA_DIR / "facilities.csv"),
        "services": pd.read_csv(SAMPLE_DATA_DIR / "services.csv"),
        "units": pd.read_csv(SAMPLE_DATA_DIR / "units.csv"),
        "unit_changes": pd.read_csv(SAMPLE_DATA_DIR / "unit_changes.csv", parse_dates=["event_ts"]),
        "diagnoses": pd.read_csv(SAMPLE_DATA_DIR / "diagnoses.csv"),
        "population_growth": pd.read_csv(SAMPLE_DATA_DIR / "population_growth.csv"),
        "capacity": pd.read_csv(SAMPLE_DATA_DIR / "capacity.csv", parse_dates=["capacity_date"]),
    }


def read_prepared_dashboard_sources() -> dict[str, pd.DataFrame]:
    required_files = [
        DASHBOARD_PREPARED_DIR / "daily.csv",
        DASHBOARD_PREPARED_DIR / "pressure.csv",
        DASHBOARD_PREPARED_DIR / "quality.csv",
        DASHBOARD_PREPARED_DIR / "capacity.csv",
        DASHBOARD_PREPARED_DIR / "census.csv",
        DASHBOARD_PREPARED_DIR / "savings.csv",
        DASHBOARD_PREPARED_DIR / "demographics.csv",
        DASHBOARD_PREPARED_DIR / "demand.csv",
        DASHBOARD_PREPARED_DIR / "current_demand.csv",
        DASHBOARD_PREPARED_DIR / "projection.csv",
        DASHBOARD_PREPARED_DIR / "facility_filters.csv",
        ETL_PREPARED_DIR / "visits.csv",
        RAW_DATA_DIR / "facilities.csv",
        RAW_DATA_DIR / "services.csv",
        RAW_DATA_DIR / "units.csv",
        RAW_DATA_DIR / "diagnoses.csv",
        RAW_DATA_DIR / "population_growth.csv",
        RAW_DATA_DIR / "capacity.csv",
        RAW_DATA_DIR / "admission_chart.csv",
        RAW_DATA_DIR / "patient_events.csv",
    ]
    if not all(path.exists() for path in required_files):
        raise FileNotFoundError("Prepared dashboard data is missing.")

    visits = pd.read_csv(ETL_PREPARED_DIR / "visits.csv", parse_dates=["admission_ts", "discharge_ts"])
    admission_chart = pd.read_csv(RAW_DATA_DIR / "admission_chart.csv", parse_dates=["admission_ts"])
    patient_events = pd.read_csv(RAW_DATA_DIR / "patient_events.csv", parse_dates=["event_ts"])
    unit_changes = pd.concat(
        [
            admission_chart[
                ["visit_id", "admission_ts", "facility_id", "admitted_unit_id"]
            ].rename(
                columns={
                    "admission_ts": "event_ts",
                    "admitted_unit_id": "unit_id",
                }
            ).assign(unit_change_id=lambda frame: "ADM-" + frame["visit_id"].astype(str)),
            patient_events[patient_events["type"] == "location"]
            .rename(columns={"event_id": "unit_change_id", "value": "unit_id"})
            [["unit_change_id", "visit_id", "event_ts", "facility_id", "unit_id"]],
        ],
        ignore_index=True,
    )
    unit_changes["event_ts"] = pd.to_datetime(unit_changes["event_ts"], errors="coerce")
    unit_changes = unit_changes.sort_values(["visit_id", "event_ts", "unit_change_id"]).reset_index(drop=True)

    return {
        "daily": pd.read_csv(DASHBOARD_PREPARED_DIR / "daily.csv", parse_dates=["calendar_date"]),
        "pressure": pd.read_csv(DASHBOARD_PREPARED_DIR / "pressure.csv", parse_dates=["calendar_date"]),
        "quality": pd.read_csv(DASHBOARD_PREPARED_DIR / "quality.csv"),
        "capacity": pd.read_csv(DASHBOARD_PREPARED_DIR / "capacity.csv"),
        "census": pd.read_csv(DASHBOARD_PREPARED_DIR / "census.csv"),
        "savings": pd.read_csv(DASHBOARD_PREPARED_DIR / "savings.csv"),
        "demographics": pd.read_csv(DASHBOARD_PREPARED_DIR / "demographics.csv"),
        "demand": pd.read_csv(DASHBOARD_PREPARED_DIR / "demand.csv"),
        "current_demand": pd.read_csv(DASHBOARD_PREPARED_DIR / "current_demand.csv"),
        "projection": pd.read_csv(DASHBOARD_PREPARED_DIR / "projection.csv"),
        "facility_filters": pd.read_csv(DASHBOARD_PREPARED_DIR / "facility_filters.csv"),
        "visits": visits,
        "raw_visits": visits.copy(),
        "admission_chart": admission_chart,
        "facilities": pd.read_csv(RAW_DATA_DIR / "facilities.csv"),
        "services": pd.read_csv(RAW_DATA_DIR / "services.csv"),
        "units": pd.read_csv(RAW_DATA_DIR / "units.csv"),
        "unit_changes": unit_changes,
        "diagnoses": pd.read_csv(RAW_DATA_DIR / "diagnoses.csv"),
        "population_growth": pd.read_csv(RAW_DATA_DIR / "population_growth.csv"),
        "raw_capacity": pd.read_csv(RAW_DATA_DIR / "capacity.csv", parse_dates=["capacity_date"]),
        "patient_events": patient_events,
    }


def _reporting_window(capacity: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(capacity["capacity_date"].min())
    end = pd.Timestamp(capacity["capacity_date"].max()) + pd.to_timedelta(1, unit="D")
    return start, end


def _visits_overlapping_window(
    visits: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    admission_ts = pd.to_datetime(visits["admission_ts"], errors="coerce")
    discharge_ts = pd.to_datetime(visits["discharge_ts"], errors="coerce")
    effective_discharge = discharge_ts.where(discharge_ts.notna(), end)
    clipped = visits[
        (effective_discharge > start)
        & (admission_ts < end)
    ].copy()
    clipped["admission_ts"] = admission_ts.loc[clipped.index].clip(lower=start)
    clipped["discharge_ts"] = effective_discharge.loc[clipped.index].clip(upper=end)
    return clipped.reset_index(drop=True)


def _unit_changes_overlapping_window(
    unit_changes: pd.DataFrame,
    raw_visits: pd.DataFrame,
    visits: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    unit_changes = unit_changes.copy()
    unit_changes["event_ts"] = pd.to_datetime(unit_changes["event_ts"], errors="coerce")
    raw_visit_lookup = raw_visits.set_index("visit_id")

    for _, visit in visits.iterrows():
        visit_id = visit["visit_id"]
        admission_ts = pd.Timestamp(visit["admission_ts"])
        discharge_ts = pd.Timestamp(visit["discharge_ts"])
        visit_changes = unit_changes[unit_changes["visit_id"] == visit_id].sort_values("event_ts")
        in_window = visit_changes[
            (visit_changes["event_ts"] >= admission_ts)
            & (visit_changes["event_ts"] < discharge_ts)
        ]

        raw_admission_ts = pd.Timestamp(raw_visit_lookup.loc[visit_id, "admission_ts"])
        if admission_ts > raw_admission_ts:
            previous_changes = visit_changes[visit_changes["event_ts"] < admission_ts]
            if not previous_changes.empty and (in_window.empty or pd.Timestamp(in_window.iloc[0]["event_ts"]) > admission_ts):
                previous = previous_changes.iloc[-1].to_dict()
                previous["unit_change_id"] = f"{previous['unit_change_id']}-CLIP"
                previous["event_ts"] = admission_ts
                rows.append(previous)

        rows.extend(in_window.to_dict("records"))

    if not rows:
        return unit_changes.iloc[0:0].copy()
    return pd.DataFrame(rows, columns=unit_changes.columns)


def build_sample_marts() -> dict[str, pd.DataFrame]:
    sources = read_sample_sources()
    raw_visits = sources["visits"]
    facilities = sources["facilities"]
    services = sources["services"]
    capacity = sources["capacity"]

    reporting_start, reporting_end = _reporting_window(capacity)
    visits = _visits_overlapping_window(raw_visits, reporting_start, reporting_end)
    unit_changes = _unit_changes_overlapping_window(sources["unit_changes"], raw_visits, visits)
    snapshots = _hourly_snapshots(visits, start=reporting_start, end=reporting_end)
    grouped_snapshots = snapshots.groupby(
        ["hour_ts", "facility_id", "service_id"],
        as_index=False,
    ).agg(census=("visit_id", "nunique"))
    hourly = grouped_snapshots.merge(
        facilities[["facility_id", "facility_name"]],
        on="facility_id",
        how="left",
    )
    hourly = hourly.merge(
        services[["service_id", "service_name"]],
        on="service_id",
        how="left",
    )
    hourly["calendar_date"] = hourly["hour_ts"].dt.normalize()
    hourly["hour_of_day"] = hourly["hour_ts"].dt.hour

    daily = (
        hourly.groupby(
            ["calendar_date", "facility_id", "facility_name", "service_id", "service_name"],
            as_index=False,
        )
        .agg(average_census=("census", "mean"), peak_census=("census", "max"))
        .merge(
            capacity,
            left_on=["calendar_date", "facility_id", "service_id"],
            right_on=["capacity_date", "facility_id", "service_id"],
            how="left",
        )
    )
    daily["average_utilization"] = daily["average_census"] / daily["staffed_beds"]
    daily["peak_utilization"] = daily["peak_census"] / daily["staffed_beds"]
    daily = daily.drop(columns=["capacity_date"])

    pressure = daily.copy()
    pressure["pressure_level"] = pd.cut(
        pressure["peak_utilization"],
        bins=[-float("inf"), 0.85, 0.90, 0.95, float("inf")],
        labels=["Normal", "High", "Severe", "Critical"],
        right=False,
    ).astype(str)
    for threshold in (85, 90, 95):
        pressure[f"above_{threshold}_percent"] = pressure["peak_utilization"] >= threshold / 100

    quality = pd.DataFrame(
        [
            {
                "check_name": "visits_missing_required_fields",
                "issue_count": int(
                    visits[
                        [
                            "visit_id",
                            "patient_id",
                            "facility_id",
                            "service_id",
                            "diagnosis_code",
                            "age",
                            "gender",
                            "admission_ts",
                            "discharge_ts",
                        ]
                    ]
                    .isna()
                    .any(axis=1)
                    .sum()
                ),
                "severity": "error",
            },
            {
                "check_name": "visits_with_invalid_date_range",
                "issue_count": int((visits["discharge_ts"] <= visits["admission_ts"]).sum()),
                "severity": "error",
            },
            {
                "check_name": "capacity_missing_or_nonpositive",
                "issue_count": int((capacity["staffed_beds"].isna() | (capacity["staffed_beds"] <= 0)).sum()),
                "severity": "warning",
            },
            {
                "check_name": "utilization_rows_without_capacity",
                "issue_count": int(daily["staffed_beds"].isna().sum()),
                "severity": "warning",
            },
        ]
    )
    quality["status"] = quality["issue_count"].map(lambda count: "pass" if count == 0 else "warn")
    return {
        "hourly": hourly,
        "daily": daily,
        "pressure": pressure,
        "quality": quality,
        "raw_visits": raw_visits,
        **sources,
        "visits": visits,
        "unit_changes": unit_changes,
    }


def load_dashboard_data() -> tuple[dict[str, pd.DataFrame], str]:
    try:
        return read_prepared_dashboard_sources(), "prepared container-local pipeline data"
    except Exception:
        return build_sample_marts(), "built-in synthetic CSV data"
