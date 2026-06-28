---
title: "Healthcare Capacity Analytics Pipeline"
summary: "Beginning Azure-style demo structure for a synthetic hospital capacity analytics pipeline with Python generation, dbt SQL models, validation, and dashboard outputs."
focusAreas:
  - Python ETL
  - Azure SQL
  - Data quality
  - Capacity analytics
azureServices:
  - Azure Blob Storage
  - Azure Functions
  - Azure SQL Database
  - Azure Static Web Apps
status: "Beginning draft"
---

## Objective
Design a synthetic healthcare capacity analytics workflow that demonstrates ingestion, transformation, validation, and reporting patterns without using patient data, internal SHA data, or private operational numbers. The current draft has been imported into `demos/healthcare-capacity/` as the starting Azure-style project structure.

## Synthetic data design
The beginning draft includes synthetic CSV samples for facilities, services, capacity, and visits. Values use generated IDs, fake facility names, and generic service labels so the workflow can be developed publicly.

## Azure services used
Planned services include Azure Blob Storage for safe sample files, Azure Function Python ETL for scheduled processing, Azure SQL Database for curated tables, and Azure Static Web Apps for public documentation. Placeholder notes now live under `demos/healthcare-capacity/azure/`.

## Pipeline architecture
The current local draft is synthetic CSVs to PostgreSQL raw tables, dbt transformations, and Streamlit dashboard outputs. The planned Azure version is synthetic Blob Storage files to Python Azure Function validation/loading, Azure SQL models, and public dashboard/report outputs.

## Transformation logic
Current draft transformations include dbt staging models, hourly calendar expansion, visit-hour expansion, enriched hourly snapshots, hourly census, daily utilization, service capacity pressure, and data quality summaries.

## Validation checks
Current and planned checks include schema conformance, required fields, valid visit date ranges, nonnegative capacity measures, dbt tests, duplicate detection, and dashboard-facing quality summaries.

## Output tables / reports
Current draft outputs include dbt mart models such as hourly census, daily utilization, service capacity pressure, and data quality summary tables. Azure SQL adaptation is the next step.

## Dashboard or visual output
The imported dashboard draft is under `demos/healthcare-capacity/dashboard/streamlit/`. Future public visuals should be exported from synthetic data only.

Local interactive dashboard:

<p><a class="button" href="http://localhost:8501" target="_blank" rel="noreferrer">Open Streamlit dashboard</a></p>

## Code repository / files
Code now lives under `demos/healthcare-capacity/`, including `etl/`, `sql/`, `dashboard/`, `data/synthetic/`, `tests/`, `config/`, `ci/`, `docs/`, and `azure/`.

## Future improvements
Convert local PostgreSQL/dbt assumptions toward Azure SQL, shape the Python loader into an Azure Function ETL module, add Blob Storage conventions, export synthetic dashboard screenshots, and add deployment notes.
