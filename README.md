# Personal Portfolio

This repository contains the Astro public website for Qiankang Wang's personal project portfolio.

Project implementations live in their own repositories. This site links out to those apps, reports, and codebases instead of carrying their implementation files inside the website repo.

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
- Azure Static Web Apps hosting

## Project Structure

```text
/
├── public/
│   └── favicon.svg
├── src/
│   ├── content/
│   │   └── projects/
│   ├── layouts/
│   └── pages/
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

- Hospital Capacity Analytics App
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
- Code repository / app link
- Future improvements
