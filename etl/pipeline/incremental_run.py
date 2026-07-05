

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

CONTAINER_DATA_ROOT = PROJECT_ROOT / "data" / "container"
RAW_DATA_DIR = CONTAINER_DATA_ROOT / "raw"
BACKUP_DATA_DIR = CONTAINER_DATA_ROOT / "backup"
REPORT_DATA_DIR = CONTAINER_DATA_ROOT / "reports"
ETL_PREPARED_DIR = PROJECT_ROOT / "data" / "etl_prepared"
DASHBOARD_PREPARED_DIR = PROJECT_ROOT / "data" / "dashboard_prepared"

from etl.event_editor.editor import next_number
from etl.pipeline.initialize_demo_dataset import run_etl_from_existing_raw
from etl.synthetic_data_generator.generate_fake_data import (
    GeneratorConfig,
    build_admission_chart,
    build_patient_events,
    build_patients_table,
    generate_capacity,
    generate_next_run_active_visits,
    generate_unit_changes,
    generate_visits,
    write_csvs
)

@dataclass
class SimulationState:
    last_generated_date: str
    next_visit_number: int
    next_patient_number: int
    next_event_number: int

class IncrementalDataError(Exception):
    """Exception raised for errors in the Incremental Refresh."""
    pass


def load_simulation_state():
    capacity_table = pd.read_csv(RAW_DATA_DIR / "capacity.csv")
    lastest_date = capacity_table["capacity_date"].max()

    admission_chart = pd.read_csv(RAW_DATA_DIR / "admission_chart.csv")
    next_visit_id = next_number(admission_chart, "visit_id", "ENC-")

    patient_table = pd.read_csv(RAW_DATA_DIR / "patients.csv")
    next_patient_id = next_number(patient_table, "patient_id", "PAT-")


    event_table = pd.read_csv(RAW_DATA_DIR / "patient_events.csv")
    next_event_id = next_number(event_table, "event_id", "EVT-")

    state = SimulationState(
        last_generated_date = lastest_date,
        next_visit_number=next_visit_id,
        next_patient_number=next_patient_id,
        next_event_number = next_event_id
        )
    return state


def generate_next_run_raw(seed: int, length: int = 1) -> dict[str, pd.DataFrame]:
    units = pd.read_csv(RAW_DATA_DIR / "units.csv")
    diagnoses = pd.read_csv(RAW_DATA_DIR / "diagnoses.csv")
    # admission_chart = pd.read_csv(RAW_DATA_DIR / "admission_chart.csv")
    facilities = pd.read_csv(RAW_DATA_DIR / "facilities.csv")
    state = load_simulation_state()
    start = pd.Timestamp(state.last_generated_date) + pd.Timedelta(days=1)
    start_string = f"{start:%Y-%m-%d}"

    new_config = GeneratorConfig(
        start_date=start_string,
        days=length,
        seed=seed,
        lookback_days=0,
        event_id = state.next_event_number,
        patient_id=state.next_patient_number,
        visit_id=state.next_visit_number

    )
    new_capacity = generate_capacity(new_config)
    new_visits = generate_visits(new_config, new_capacity)
    new_unit_changes = generate_unit_changes(new_config, new_visits, units)
    new_admission_chart = build_admission_chart(new_visits, new_unit_changes)
    new_patients = build_patients_table(new_visits, facilities)

    active_visits = generate_next_run_active_visits(
        new_config,
        length,
        target_discharges=len(new_admission_chart),
    )
    active_unit_changes = generate_unit_changes(new_config, active_visits, units)
    new_events = build_patient_events(new_config, pd.concat([active_visits, new_visits]), pd.concat([active_unit_changes, new_unit_changes]), diagnoses)
    run_start = pd.Timestamp(new_config.start_date)
    run_end = run_start + pd.Timedelta(days=new_config.days)
    new_events["event_ts"] = pd.to_datetime(new_events["event_ts"], errors="coerce")
    new_events = new_events.loc[
        (new_events["event_ts"] >= run_start)
        & (new_events["event_ts"] < run_end)
    ].reset_index(drop=True)

    return {"capacity": new_capacity, "patients": new_patients, "admission_chart": new_admission_chart, "patient_events": new_events}

def log_incremental(tables: dict[str, pd.DataFrame]) -> str:
    REPORT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logged_at = pd.Timestamp.now().floor("s")

    capacity = tables.get("capacity", pd.DataFrame())
    admissions = tables.get("admission_chart", pd.DataFrame())
    events = tables.get("patient_events", pd.DataFrame())

    simulated_dates = pd.to_datetime(capacity.get("capacity_date", pd.Series(dtype="object")), errors="coerce")
    admission_times = pd.to_datetime(admissions.get("admission_ts", pd.Series(dtype="object")), errors="coerce")
    event_times = pd.to_datetime(events.get("event_ts", pd.Series(dtype="object")), errors="coerce")

    status = "success"
    if any(frame.empty for frame in (capacity, admissions, events)):
        status = "warning"

    summary = {
        "run_logged_at": logged_at.isoformat(),
        "status": status,
        "simulated_start_date": simulated_dates.min().date().isoformat() if simulated_dates.notna().any() else "",
        "simulated_end_date": simulated_dates.max().date().isoformat() if simulated_dates.notna().any() else "",
        "capacity_rows": int(len(capacity)),
        "patient_rows": int(len(tables.get("patients", pd.DataFrame()))),
        "admission_rows": int(len(admissions)),
        "event_rows": int(len(events)),
        "first_admission_ts": admission_times.min().isoformat() if admission_times.notna().any() else "",
        "last_admission_ts": admission_times.max().isoformat() if admission_times.notna().any() else "",
        "first_event_ts": event_times.min().isoformat() if event_times.notna().any() else "",
        "last_event_ts": event_times.max().isoformat() if event_times.notna().any() else "",
    }

    log_path = REPORT_DATA_DIR / "incremental_runs.csv"
    log_row = pd.DataFrame([summary])
    if log_path.exists():
        existing_log = pd.read_csv(log_path)
        log_row = pd.concat([existing_log, log_row], ignore_index=True)
    log_row.to_csv(log_path, index=False)

    latest_path = REPORT_DATA_DIR / "latest_incremental_run.json"
    latest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return json.dumps(summary, indent=2)

INCREMENTAL_UNIQUE_KEYS = {
    "capacity": ["capacity_date", "facility_id", "service_id"],
    "patients": ["patient_id"],
    "admission_chart": ["visit_id"],
    "patient_events": ["event_id"],
}


def check_incremental(table_name: str, current_table: pd.DataFrame, new_table: pd.DataFrame) -> bool:
    unique_keys = INCREMENTAL_UNIQUE_KEYS.get(table_name)
    if unique_keys is None:
        raise IncrementalDataError(f"No incremental unique key configured for {table_name} table")

    missing_columns = [column for column in unique_keys if column not in current_table.columns or column not in new_table.columns]
    if missing_columns:
        raise IncrementalDataError(
            f"Missing incremental key columns for {table_name} table: {', '.join(missing_columns)}"
        )

    if new_table.empty:
        return True

    duplicated_delta = new_table.duplicated(unique_keys, keep=False)
    if duplicated_delta.any():
        duplicate_count = int(duplicated_delta.sum())
        raise IncrementalDataError(
            f"{table_name} delta contains {duplicate_count} duplicate rows for key {unique_keys}"
        )

    current_keys = current_table[unique_keys].astype(str)
    new_keys = new_table[unique_keys].astype(str)
    current_key_values = set(map(tuple, current_keys.to_numpy()))
    overlap_count = sum(tuple(row) in current_key_values for row in new_keys.to_numpy())
    if overlap_count:
        raise IncrementalDataError(
            f"{table_name} delta overlaps existing raw data on {overlap_count} rows for key {unique_keys}"
        )

    return True


def ensure_patient_registration_date(patients: pd.DataFrame) -> pd.DataFrame:
    if "registration_date" in patients.columns:
        return patients

    admission_chart = pd.read_csv(RAW_DATA_DIR / "admission_chart.csv", parse_dates=["admission_ts"])
    first_registration = (
        admission_chart.sort_values("admission_ts")
        .drop_duplicates("patient_id", keep="first")
        .assign(registration_date=lambda frame: frame["admission_ts"].dt.date)
        [["patient_id", "registration_date"]]
    )
    patients = patients.merge(first_registration, on="patient_id", how="left")
    column_order = ["patient_id", "registration_date", "age", "gender", "region"]
    remaining_columns = [column for column in patients.columns if column not in column_order]
    return patients[[column for column in column_order if column in patients.columns] + remaining_columns]


def etl_incremental(seed: int, length: int = 1) -> str:
    delta_tables = generate_next_run_raw(seed, length)
    updated_tables = {}

    for name, delta_table in delta_tables.items():
        current = pd.read_csv(RAW_DATA_DIR / f"{name}.csv")
        if name == "patients":
            current = ensure_patient_registration_date(current)
        check_incremental(name, current, delta_table)
        updated_tables[name] = pd.concat([current, delta_table], ignore_index=True)

    write_csvs(updated_tables, RAW_DATA_DIR)
    run_etl_from_existing_raw()
    log = log_incremental(delta_tables)
    return log
