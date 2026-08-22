"""Runtime lifecycle helpers for the Streamlit demo dataset."""

from __future__ import annotations

from collections.abc import MutableMapping

from etl.pipeline.initialize_demo_dataset import PipelineResult, run_fake_data_pipeline
from etl.pipeline.paths import (
    DASHBOARD_PREPARED_DIR,
    ETL_PREPARED_DIR,
    RAW_DATA_DIR,
    RUN_HISTORY_PATH,
)


DEMO_INITIALIZED_SESSION_KEY = "demo_initialized_on_open_v1"
REQUIRED_RUNTIME_FILES = [
    RAW_DATA_DIR / "patients.csv",
    RAW_DATA_DIR / "admission_chart.csv",
    RAW_DATA_DIR / "patient_events.csv",
    ETL_PREPARED_DIR / "visits.csv",
    ETL_PREPARED_DIR / "unit_changes.csv",
    DASHBOARD_PREPARED_DIR / "daily.csv",
    DASHBOARD_PREPARED_DIR / "pressure.csv",
    RUN_HISTORY_PATH,
]


def runtime_data_exists() -> bool:
    """Return whether the app has enough prepared data to render without bootstrapping."""
    return all(path.exists() for path in REQUIRED_RUNTIME_FILES)


def reset_demo_session(seed: int = 42) -> PipelineResult:
    """Regenerate the demo runtime dataset and start a fresh job history."""
    return run_fake_data_pipeline(seed=seed)


def initialize_demo_session_once(session_state: MutableMapping[str, object], seed: int = 42) -> PipelineResult | None:
    """Ensure demo data exists once per UI session without running ETL on page load."""
    if session_state.get(DEMO_INITIALIZED_SESSION_KEY):
        return None

    result = None if runtime_data_exists() else run_fake_data_pipeline(seed=seed)
    session_state[DEMO_INITIALIZED_SESSION_KEY] = True
    return result
