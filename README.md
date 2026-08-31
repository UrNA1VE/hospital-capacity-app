# Hospital Capacity Analytics App

A Streamlit application for exploring a synthetic hospital-capacity analytics workflow.

The app lets users initialize a sample dataset, append incremental daily data, edit raw source records, review table quality, and explore dashboard-ready capacity analytics.

## Data Safety

This project uses synthetic data only. Do not add real patient data, internal operational data, credentials, private screenshots, or confidential documents.

## Run Locally

Create and activate a virtual environment:

```sh
cd /Users/qiankangwang/Desktop/hospital-capacity-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the app:

```sh
streamlit run dashboard/streamlit/Home.py
```

Open:

```text
http://localhost:8501
```

If `streamlit` is not found, run:

```sh
.venv/bin/streamlit run dashboard/streamlit/Home.py
```

## Use The App

Use the home page actions to control the dataset:

- **Initialize Dataset** creates a fresh 10-day synthetic dataset.
- **Incremental Run** appends the next simulated day and refreshes the app outputs.
- **Clear Runtime** removes generated runtime data, prepared outputs, reports, and job history.

Use the app pages for the main workflows:

- **Data Explorer**: browse raw, prepared, dashboard, and job-history tables.
- **User Editor**: edit raw records, submit changes, and undo the latest edit job.
- **Dashboard**: review census, capacity pressure, demand, and bed projection views.
- **Patient Journey**: inspect one patient encounter across admission, movement, service, diagnosis, and discharge events.

## Run With Docker

Build and start the local container:

```sh
docker compose up --build
```

Open:

```text
http://localhost:8501
```

Stop the container:

```sh
docker compose down
```

## Regenerate Data From The CLI

Generate raw synthetic CSVs:

```sh
python etl/synthetic_data_generator/data_generator.py
```

Initialize raw data and rebuild app outputs:

```sh
python etl/pipeline/initialize_dataset.py
```

## Run Tests

```sh
pytest tests/python
```
