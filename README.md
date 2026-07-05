# Healthcare Capacity Analytics Pipeline

Synthetic hospital capacity analytics demo.

This project is a public-safe technical demo. It combines a Python synthetic data generator, container-local raw data, validation reports, derived encounter tables, dashboard-prepared outputs, and a Streamlit dashboard. The local version does not use persistent cloud storage; data edits are intended for demo sessions only.

The raw generated layer is event-level. It stores patient demographics in `patients.csv` and hospital activity in `patient_events.csv`; visit-level tables are derived during ETL rather than stored as raw source files.

## Current status

This project is under active development. The original draft is preserved as source material under `docs/original-draft-readme.md`, and its sanitized migration plan is under `docs/sanitized-migration-plan.md`.

## Data safety boundary

All demo data must remain synthetic or explicitly public-safe.

Do not add real SHA data, patient data, internal screenshots, internal table names, private operational numbers, credentials, local network paths, or confidential documents.

## Project layout

```text
hospital-capacity-app/
├── ci/                        Draft CI workflow reference
├── config/                    Safe environment/profile examples only
├── dashboard/streamlit/       Current dashboard draft
├── data/synthetic/            Synthetic CSV samples
├── data/container/            Container-local raw, backup, and report data
├── data/etl_prepared/         Derived visit-level ETL output
├── data/dashboard_prepared/   Aggregated dashboard output destination
├── docs/                      Draft documentation and migration notes
├── etl/event_editor/          Raw event editor helpers
├── etl/pipeline/              Local ETL pipeline runners
├── etl/synthetic_data_generator/
├── notebooks/
└── tests/python/
```

## Current local workflow

Install Python dependencies from this folder:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Generate synthetic CSV files:

```sh
python etl/synthetic_data_generator/generate_fake_data.py
```

The generated raw source files include:

```text
patients.csv
admission_chart.csv
patient_events.csv
facilities.csv
services.csv
units.csv
diagnoses.csv
capacity.csv
population_growth.csv
```

`admission_chart.csv` stores one admission/start-state row per visit, including admitted unit, service, diagnosis, facility, admission time, and admission type. `patient_events.csv` stores updates after admission with `type` values of `location`, `service`, `diagnosis`, and `discharge`. Open inpatient encounters simply do not have a discharge event. The ETL derives analytical `visits` from admission chart rows plus the latest service, diagnosis, location, and discharge events.

Initialize the local demo dataset and rebuild the DuckDB/dashboard-prepared outputs:

```sh
python etl/pipeline/initialize_demo_dataset.py
```

Each run clears the previous container-local raw/report files and overwrites `data/dashboard_prepared/` with the latest aggregated outputs to limit local storage use.

The ETL also writes derived visit-level tables to:

```text
data/etl_prepared/
└── visits.csv
```

Run the Streamlit dashboard draft:

```sh
streamlit run dashboard/streamlit/Home.py
```

Run the same dashboard in a local container:

```sh
docker compose up --build
```

Then open:

```text
http://localhost:8501
```

The local compose setup mounts `./data` into the container, so generated raw files, backup files, ETL outputs, and dashboard-prepared CSVs remain available on your machine after the container stops.

Stop the local container:

```sh
docker compose down
```

Run Python tests:

```sh
pytest tests/python
```

## Pipeline workflow

The local demo has two run modes:

- `initialize_demo_dataset.py` performs a full demo refresh. It regenerates synthetic raw files, validates the source data, rebuilds derived encounter tables, and rewrites dashboard-ready outputs.
- `incremental_run.py` simulates the next day of activity. It appends new raw rows to selected source tables, validates the incremental batch, then rebuilds the derived/dashboard tables from the full raw history.

```text
Synthetic generator config
  seed, start date, duration, ID counters
        |
        v
Raw source layer
  data/container/raw/
  - patients.csv
  - admission_chart.csv
  - patient_events.csv
  - capacity.csv
  - facilities.csv
  - services.csv
  - units.csv
  - diagnoses.csv
  - population_growth.csv
        |
        v
Data checks
  data/container/reports/data_check_report.csv
  - required columns
  - unique visit IDs
  - admission/discharge date logic
  - capacity values
  - facility/service/diagnosis references
  - active open inpatient records
        |
        v
Encounter ETL
  data/etl_prepared/
  - visits.csv

  Derived in memory during ETL:
  - unit_changes
        |
        v
Dashboard marts
  data/dashboard_prepared/
  - daily.csv
  - census.csv
  - pressure.csv
  - capacity.csv
  - demand.csv
  - current_demand.csv
  - projection.csv
  - savings.csv
  - demographics.csv
  - quality.csv
  - facility_filters.csv
        |
        v
Streamlit app
  dashboard/streamlit/Home.py
  dashboard/streamlit/pages/
```

### Incremental model

The incremental model treats the raw event layer as the source of truth:

```text
Current raw history
        |
        v
Find latest simulated date and next IDs
        |
        v
Generate one new simulated day
        |
        v
Append only to raw source files
  - patients.csv
  - admission_chart.csv
  - patient_events.csv
  - capacity.csv
        |
        v
Validate duplicate keys and overlap with existing raw rows
        |
        v
Rebuild derived encounter/dashboard outputs
```

`visits.csv` is not maintained as an incremental source table. It is rebuilt from `admission_chart.csv` and `patient_events.csv` so the dashboard always reflects the complete event history, including late discharge events for existing active visits.

### Data check layer

The data check layer exists in two places:

- `data/container/reports/data_check_report.csv` is written during the local pipeline run.
- `data/dashboard_prepared/quality.csv` is the dashboard-facing copy used by the Data Quality page.

The Streamlit home page shows a compact pipeline status summary. The full check details live in the **Data Quality** page and in the CSV reports above.
