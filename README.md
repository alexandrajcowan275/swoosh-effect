# The Swoosh Effect

Do Nike-sponsored college athletic departments win more, and did Nike make them winners or just sign them? 8 seasons of NCAA Directors' Cup data, SQL, regression, and machine learning.

Built by [Alexandra Cowan](https://www.linkedin.com/in/alexandra-cowan-24705331b/).

[![CI](https://github.com/alexandrajcowan275/swoosh-effect/actions/workflows/ci.yml/badge.svg)](https://github.com/alexandrajcowan275/swoosh-effect/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Tableau dashboard](https://public.tableau.com/views/TheSwooshEffect/TheSwooshEffect)

## Why I built this

As a former D1 rower, I only wanted to row for a Nike school, so I tested whether Nike schools actually win more.

## Key findings

- **The best programs wear Nike** (A+B = seasons with direct sponsor evidence): Top-10 finish rates are **21.1% for Nike (61/289 school-seasons)**, **3.5% for Under Armour (3/86)** and **2.4% for adidas (2/85)**. These are within-brand rates. [Source](reports/brand_summary.csv).
- **Pick or make (A+B):** Nike schools' average percentile lead is **2.67 points over adidas** and **3.72 over Under Armour**. On the same model sample, accounting for last season's performance shrinks the adjusted lead by **56–62%**: consistent with Nike signing already-strong programs, not proof that Nike makes them better. [Mean gaps and model comparison](docs/methodology.md#brand-comparisons).
- **Predicting next season:** Last season's performance is the **#1 predictor (of 43 features)**. Across the broader study's **712 held-out school-seasons**, no model, including LightGBM, clearly beat simply predicting last season's result **on mean absolute error** (MAE **11.08 baseline vs 11.12 OLS vs 11.18 LightGBM**). [Results, including RMSE improvements](docs/methodology.md#machine-learning-benchmark) · [Importance](reports/ml/permutation_importance.csv).

![Top-10 finish rates within each major provider's covered school-seasons using direct sponsor evidence A+B, with sample counts](docs/images/top10_finish_rates.png)

## How it works

```mermaid
flowchart LR
    A["Directors' Cup PDFs"] --> B["Python parser"]
    B --> C["DuckDB + SQL"]
    C --> D["OLS + LightGBM"]
    D --> E["Tableau Public"]
```

| Layer | Tools | Purpose |
|---|---|---|
| Parsing | Python, pdfplumber | Extract and validate standings |
| Data | pandas, DuckDB, SQL | Join school-seasons and audit evidence |
| Statistics | statsmodels | Compare brands with clustered OLS and performance lags |
| ML | LightGBM, scikit-learn | Forecast with time-based validation and permutation importance |
| Delivery | pytest, GitHub Actions, Docker, Tableau | Test, reproduce and explore results |

## Quickstart

From a cloned repository. Local prerequisites: **Python 3.12** and an OpenMP runtime (`libomp` on macOS, `libgomp1` on Linux); Docker includes both. [Setup and full PDF rebuild](docs/methodology.md#how-to-run).

**Local — rebuild from committed, audited CSVs and run all tests:**

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHON=.venv/bin/python ./run.sh --offline
```

**Docker — with a running Docker engine:**

```bash
docker build -t swoosh-effect .
docker run --rm --network none swoosh-effect
```

## Methodology & limitations

- The selected department cohort is not a D1 census; brand rates are not national market shares. [Scope and sources](docs/data_sources.md).
- The separate A+B+C analysis adds bounded continuity inference. Unknown brands stay unknown. [Evidence rules](docs/methodology.md#evidence-and-coverage).
- Observational models cannot establish causation; budgets, sport offerings and prior provider exposure can confound results. [Models](docs/methodology.md#models-and-sample-sizes).
- Forecasts use time-based splits and pre-season inputs. Masked brands and historical source revisions limit interpretation. [ML methods](docs/methodology.md#machine-learning-benchmark).
- COVID, realignment and coaching changes complicate switch case studies. [Full limitations](docs/methodology.md#limitations-and-remaining-unknowns) · [Release audit](docs/release_audit.md) · [Number ledger](docs/readme_number_ledger.csv).

## Repo structure

```text
.github/   CI tests and publication checks
data/      Audited observations, evidence and source manifests
src/       Parsers, handwritten algorithms, statistical models and ML
sql/       Database views and descriptive summaries
scripts/   Secret/URL checks and synthetic fixture utilities
tests/     Parser, evidence, regression, forecasting and security checks
reports/   Generated findings, charts and model outputs
exports/   Tableau-ready CSVs and data dictionary
docs/      Methodology, data sources, dashboard guide and audit records
notebooks/ Exploratory analysis
```

Independent student project. Not affiliated with or endorsed by Nike, Inc.
