"""Runtime lifecycle helpers for the Streamlit demo dataset."""

from __future__ import annotations

from collections.abc import MutableMapping

from etl.pipeline.initialize_demo_dataset import PipelineResult, reset_demo_runtime, run_fake_data_pipeline


DEMO_INITIALIZED_SESSION_KEY = "demo_initialized_on_open_v1"


def reset_demo_session(seed: int = 42) -> PipelineResult:
    """Clear runtime data/logs and create a fresh initial demo dataset."""
    reset_demo_runtime()
    return run_fake_data_pipeline(seed=seed)


def initialize_demo_session_once(session_state: MutableMapping[str, object], seed: int = 42) -> PipelineResult | None:
    """Create initial demo data once per UI session and log the initial job."""
    if session_state.get(DEMO_INITIALIZED_SESSION_KEY):
        return None

    result = reset_demo_session(seed=seed)
    session_state[DEMO_INITIALIZED_SESSION_KEY] = True
    return result
