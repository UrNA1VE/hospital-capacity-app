---
title: "Hospital Capacity Analytics App"
summary: "Standalone hospital capacity analytics app with synthetic data, Python ETL, dbt-style SQL modelling, validation, and dashboard-ready outputs."
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
status: "Standalone app repo"
---

## Objective
Design a synthetic healthcare capacity analytics workflow that demonstrates ingestion, transformation, validation, and reporting patterns without using patient data, internal SHA data, or private operational numbers. The implementation is maintained separately from this Astro website.

## Synthetic data design
The beginning draft includes synthetic CSV samples for facilities, services, capacity, and visits. Values use generated IDs, fake facility names, and generic service labels so the workflow can be developed publicly.

## Azure services used
Planned and demonstrated services include Azure Blob Storage for safe sample files, Python ETL workflows, Azure SQL-style curated tables, containerized dashboard deployment, and Azure Static Web Apps for this public portfolio.

## Pipeline architecture
The current local draft is synthetic CSVs to PostgreSQL raw tables, dbt transformations, and Streamlit dashboard outputs. The planned Azure version is synthetic Blob Storage files to Python Azure Function validation/loading, Azure SQL models, and public dashboard/report outputs.

## Transformation logic
Current draft transformations include dbt staging models, hourly calendar expansion, visit-hour expansion, enriched hourly snapshots, hourly census, daily utilization, service capacity pressure, and data quality summaries.

## Validation checks
Current and planned checks include schema conformance, required fields, valid visit date ranges, nonnegative capacity measures, dbt tests, duplicate detection, and dashboard-facing quality summaries.

## Output tables / reports
Current draft outputs include dbt mart models such as hourly census, daily utilization, service capacity pressure, and data quality summary tables. Azure SQL adaptation is the next step.

## Dashboard or visual output
The public dashboard is deployed separately from this portfolio and uses synthetic data only.

<p><a class="button" href="https://healthcare-capacity-dashboard.thankfulpond-179d04d0.centralus.azurecontainerapps.io" target="_blank" rel="noreferrer">Open deployed app</a></p>

## Code repository / files
Code now lives in the standalone repository: <a href="https://github.com/UrNA1VE/hospital-capacity-app" target="_blank" rel="noreferrer">UrNA1VE/hospital-capacity-app</a>.

## Future improvements
Convert local PostgreSQL/dbt assumptions toward Azure SQL, shape the Python loader into an Azure Function ETL module, add Blob Storage conventions, export synthetic dashboard screenshots, and add deployment notes.
