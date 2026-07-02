---
title: "GCR Computational Analysis"
summary: "Computational implementation work for generalized crack random number generation, density evaluation, parameter estimation, and goodness-of-fit routines."
focusAreas:
  - Simulation
  - Parameter estimation
  - EM algorithm
  - Goodness-of-fit testing
azureServices:
  - Azure Static Web Apps
status: "Contribution scoped"
---

## Objective
Document only the computational portion of the generalized crack distribution project. The portfolio page should make the contribution boundary explicit: the showcased work is implementation, simulation, parameter estimation, and diagnostic computation.

## Contribution boundary
My demonstrated contribution is the computational layer: R implementations for random-number generation, density functions, MLE, method-of-moments estimation, EM-style estimation, and goodness-of-fit routines. The page should not imply sole ownership of the full theory, proposal, or written project direction.

## Synthetic data design
No public dataset is required for the current page. The computational work is simulation-based and can generate samples from the implemented distribution routines.

## Azure services used
The current portfolio need is documentation through Static Web Apps. No deployed data service is required for this computational case study.

## Pipeline architecture
The public-safe computational project now lives in the standalone `UrNA1VE/gcr-computational-analysis` repository, with cleaned scripts, reports, and example simulation outputs separated from this portfolio site.

## Transformation logic
The computational workflow defines component random generators, combines them into generalized crack samples, evaluates density functions, and estimates parameters through multiple numerical strategies.

## Validation checks
The existing work checks estimates through repeated simulation, compares estimated and true densities, and includes goodness-of-fit logic for generated samples.

## Output tables / reports
Portfolio-ready outputs should include parameter-estimation summaries, simulation distributions, density overlays, and goodness-of-fit tables generated from simulated data.

## Dashboard or visual output
A future Streamlit or static visual demo could expose sliders for distribution parameters and show simulated density curves, fitted estimates, and goodness-of-fit summaries.

## Code repository / files
Original local references inspected:

- `Desktop/GCR-project/EM_GCR.R`
- `Desktop/GCR-project/MOM_GCR.R`
- `Desktop/GCR-project/GCR&ParameterEstimation.Rmd`
- `Desktop/GCR-project/GCR&goodnessOfFit.R`

## Future improvements
Create a cleaned public demo folder with contribution notes, reproducible simulation seeds, lightweight examples, and screenshots that focus only on the computational implementation.
