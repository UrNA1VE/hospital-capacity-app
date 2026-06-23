# Azure Data Project Platform

This repository contains an Astro public website for showcasing deployed technical data projects. The site is designed as an Azure-hosted technical project platform, not a resume-style portfolio.

The platform focuses on SQL, Python/R, Azure data pipelines, dashboards, data quality validation, analytics engineering, and reproducible methods.

## Data Safety

All datasets, screenshots, schemas, table names, metrics, and dashboard outputs used in this repository must be synthetic or public-safe.

Do not add:

- Real SHA data
- Patient data
- Internal screenshots
- Internal table names
- Private operational numbers
- Confidential documents
- Behavioral interview content
- Resume-style job descriptions

## Tech Stack

- Astro
- TypeScript-flavored Astro content collections
- Static HTML/CSS output
- Planned Azure Static Web Apps hosting
- Planned Azure Blob Storage sample assets
- Planned Azure Function Python ETL demos
- Planned Azure SQL Database reporting models

## Project Structure

```text
/
├── demos/
│   ├── data-quality/
│   ├── graduate-statistics/
│   ├── healthcare-capacity/
│   ├── recruitment-analytics/
│   └── sql-optimization/
├── public/
│   └── images/
├── src/
│   ├── content/
│   │   └── projects/
│   ├── layouts/
│   └── pages/
│       └── projects/
└── package.json
```

## Run Locally

Install dependencies:

```sh
npm install
```

Start the Astro development server in background mode:

```sh
astro dev --background
```

Manage the background server:

```sh
astro dev status
astro dev logs
astro dev stop
```

## Build

```sh
npm run build
```

The production site is generated in `dist/`.

## Future Azure Static Web Apps Deployment

Use these settings when configuring Azure Static Web Apps:

- App location: `/`
- API location: blank
- Output location: `dist`

## Planned Project Areas

- Healthcare Capacity Analytics Pipeline
- Recruitment Process Analytics Dashboard
- SQL Reporting Optimization Demo
- Data Quality Validation Framework
- Graduate Statistics / Data Science Project

Each project page follows this technical structure:

- Objective
- Synthetic data design
- Azure services used
- Pipeline architecture
- Transformation logic
- Validation checks
- Output tables / reports
- Dashboard or visual output
- Code repository / files
- Future improvements
