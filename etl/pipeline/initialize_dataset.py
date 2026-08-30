"""Initialize the container-local dataset for the dashboard."""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from etl.pipeline.job_logger import EtlJob  # noqa: E402
from etl.pipeline.mart_layer import generate_mart_layer  # noqa: E402
from etl.pipeline.paths import (  # noqa: E402
    BACKUP_DATA_DIR,
    DASHBOARD_PREPARED_DIR,
    ETL_PREPARED_DIR,
    LOG_DATA_DIR,
    RAW_DATA_DIR,
    REPORT_DATA_DIR,
)
from etl.synthetic_data_generator.generate_fake_data import GeneratorConfig, initial_fake_data, write_csvs  # noqa: E402


@dataclass(frozen=True)
class PipelineResult:
    seed: int
    raw_dir: str
    report_dir: str
    etl_prepared_dir: str
    prepared_dir: str
    validation_status: str
    validation_issue_count: int


def clear_runtime_data() -> None:
    for folder in (
        RAW_DATA_DIR,
        BACKUP_DATA_DIR,
        REPORT_DATA_DIR,
        LOG_DATA_DIR,
        ETL_PREPARED_DIR,
        DASHBOARD_PREPARED_DIR,
    ):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)


def clear_container_run_data() -> None:
    for folder in (RAW_DATA_DIR, REPORT_DATA_DIR):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)


def generate_raw_layer(seed: int, days: int = 10, start_date: str = "2025-01-01") -> dict[str, pd.DataFrame]:
    """Generate and write the initial raw CSV layer."""
    clear_container_run_data()

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    config = GeneratorConfig(start_date=start_date, days=days, seed=seed)
    raw_tables = initial_fake_data(config)
    write_csvs(raw_tables, RAW_DATA_DIR)
    return raw_tables


def pipeline_result_json(result: PipelineResult) -> dict[str, object]:
    payload = asdict(result)
    for key in ("raw_dir", "report_dir", "etl_prepared_dir", "prepared_dir"):
        payload[key] = str(Path(payload[key]).relative_to(PROJECT_ROOT))
    return payload


def run_etl_from_existing_raw(
    job_type: str = "etl_refresh",
    params: dict[str, object] | None = None,
    log_job: bool = True,
) -> dict[str, object]:
    with EtlJob(job_type, params=params, enabled=log_job):
        return generate_mart_layer()


def initialize_dataset(seed: int, days: int = 10, start_date: str = "2025-01-01") -> PipelineResult:
    with EtlJob(
        "initial_dataset",
        params={"seed": seed, "days": days, "start_date": start_date},
    ):
        generate_raw_layer(seed=seed, days=days, start_date=start_date)
        mart_result = generate_mart_layer()

        result = PipelineResult(
            seed=seed,
            raw_dir=str(mart_result["raw_dir"]),
            report_dir=str(mart_result["report_dir"]),
            etl_prepared_dir=str(mart_result["etl_prepared_dir"]),
            prepared_dir=str(mart_result["prepared_dir"]),
            validation_status=str(mart_result["status"]),
            validation_issue_count=int(mart_result["issue_count"]),
        )

        (REPORT_DATA_DIR / "pipeline_result.json").write_text(
            json.dumps(pipeline_result_json(result), indent=2),
            encoding="utf-8",
        )
        return result


if __name__ == "__main__":
    initialized = initialize_dataset(seed=42)
    print(json.dumps(asdict(initialized), indent=2))
