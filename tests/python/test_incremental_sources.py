from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from etl.pipeline import incremental_run
from etl.pipeline.mart_layer import build_encounter_tables_from_events
from etl.synthetic_data_generator import data_generator


@pytest.fixture
def sources():
    return data_generator.initial_fake_data(
        data_generator.GeneratorConfig(seed=42, days=10)
    )


def test_dataframe_batch_does_not_read_csv_or_mutate_sources(sources, monkeypatch):
    original = {name: frame.copy(deep=True) for name, frame in sources.items()}

    def unexpected_read(*args, **kwargs):
        raise AssertionError("DataFrame mode must not read CSV files")

    monkeypatch.setattr(pd, "read_csv", unexpected_read)
    batch = incremental_run.generate_next_run_raw(seed=42, sources=sources)
    assert set(batch) == {"capacity", "patients", "admission_chart", "patient_events"}
    assert all(not frame.empty for frame in batch.values())
    start = pd.Timestamp("2025-01-11")
    assert pd.to_datetime(batch["capacity"]["capacity_date"]).eq(start).all()
    assert batch["patient_events"]["event_ts"].between(
        start, start + pd.Timedelta(days=1), inclusive="left"
    ).all()
    for name, key in (("patients", "patient_id"), ("admission_chart", "visit_id"), ("patient_events", "event_id")):
        assert batch[name][key].is_unique
        assert not batch[name][key].isin(sources[name][key]).any()
    repeated = incremental_run.generate_next_run_raw(seed=42, sources=sources)
    for name in batch:
        pd.testing.assert_frame_equal(batch[name], repeated[name])
    for name in sources:
        pd.testing.assert_frame_equal(sources[name], original[name])


def test_dataframe_batch_matches_default_csv_mode(sources, tmp_path, monkeypatch):
    paths = {}
    for name, frame in sources.items():
        paths[name] = tmp_path / f"{name}.csv"
        frame.to_csv(paths[name], index=False)
    visits = build_encounter_tables_from_events(sources)["visits"]
    visits_path = tmp_path / "visits.csv"
    visits.to_csv(visits_path, index=False)
    monkeypatch.setattr(incremental_run, "RAW_TABLE_PATHS", paths)
    monkeypatch.setitem(data_generator.ETL_PREPARED_TABLE_PATHS, "visits", visits_path)
    local = incremental_run.generate_next_run_raw(seed=42)
    cloud = incremental_run.generate_next_run_raw(seed=42, sources=sources)
    for name in local:
        pd.testing.assert_frame_equal(local[name], cloud[name], check_dtype=False)


def test_empty_capacity_is_rejected(sources):
    sources["capacity"] = sources["capacity"].iloc[:0]
    with pytest.raises(ValueError, match="Capacity table is empty"):
        incremental_run.load_simulation_state(sources)
