# macro-strategy-conditioning

A research repository for diagnosing how **strategy return series** behave under different **macro regimes**.

> **Important:** This project is **not** a trading system, **not** a signal engine, and **not** a forecasting model. It is strictly a descriptive, conditional analysis framework.

## Purpose

`macro-strategy-conditioning` helps answer questions like:
- How do strategy returns differ across observed macro regimes?
- How does volatility or drawdown change by regime label?
- What behavior appears around realized macro transition dates?

The goal is interpretation and robustness diagnostics, not prediction.

## Current Status

**ACCEPTED — REAL-DATA WORKFLOW VALIDATED**

- full real-data acceptance completed on August 17, 2026
- the Alpha Generation adapter produced 141 rows across 3 strategies, and all 141 rows matched the refreshed canonical macro handoff
- the canonical 05-08 notebook workflow executed successfully in the acceptance run
- the supplied sample realized 3 macro regimes, 6 aligned transitions, 56 transitions outside coverage, and 18 strategy-transition windows split into 15 complete, 3 partial, and 0 missing
- the remaining limitations are dataset-coverage limitations, not known implementation defects
- this repository remains descriptive research infrastructure only, not forecasting or trading infrastructure

## Relationship to Part I (Macro Interface)

This repository consumes monthly macro outputs already prepared upstream.

For direct real-data placement and smoke-check instructions, see [docs/real_data_integration.md](/C:/GitHub/macro-strategy-conditioning-lab/docs/real_data_integration.md).

Current provenance note:
- the checked-in `data/macro/regimes.csv` and `data/macro/transitions.csv` files were refreshed on August 17, 2026 after the upstream Part I October 2025 transformation fix
- the historical raw monthly source referenced by the executed Part I notebooks is `C:\Users\JR\OneDrive\Mini PC\FRED\data\raw\fred_monthly.csv`
- that original OneDrive path was identifiable from notebook evidence but not directly readable from this workspace, so the refreshed handoff was rebuilt from the fixed Part I logic plus executed upstream notebook evidence for the recovered October 2025 row
- the refreshed canonical regime table now includes `2025-10-31` as `Expansion / Inflationary / Easing`, and the transition table is otherwise unchanged versus the prior handoff
- strict source-file hash comparison against those original standalone exports remains optional future provenance work

### Regime table schema
- `DATE` (month-end datetime)
- `Growth_Regime` in `{Expansion, Contraction}`
- `Inflation_Regime` in `{Inflationary, Disinflationary}`
- `Policy_Regime` in `{Tightening, Easing}`
- `Macro_Regime` as `"<Growth> / <Inflation> / <Policy>"`

### Transition table schema
- `transition_date` (datetime)
- `from` (string)
- `to` (string)

Constraints respected in this repo:
- exactly one macro regime per date
- no missing values
- no probabilities
- no forecasts
- no signal generation

## Strategy Interface (Locked)

### Required returns schema
- `DATE` (month-end datetime)
- `strategy_id` (string)
- `returns` (float)

### Optional metadata fields
- `strategy_name`
- `strategy_category`
- `asset_class`

If optional metadata is absent, the canonical final packet leaves those summary fields blank instead of failing.

Rules respected in this repo:
- strategies are treated as black-box return streams
- no positions, no execution logic
- no optimization routines

Checked-in strategy fixtures:
- `data/strategies/strategy_returns_example.csv`: narrow synthetic/sample-only fixture used to preserve sparse-coverage and zero-aligned-transition examples
- `data/strategies/strategy_returns_wide_sample.csv`: wider synthetic/sample-only fixture used to exercise broader descriptive regime coverage and aligned transition examples

External real-data adaptation path:
- `python scripts/export_alpha_generation_strategy_returns.py --input <alpha_generation_period_returns.csv> --output <fredii_strategy_returns.csv>` exports an Alpha Generation `period_returns.csv` artifact into the locked FRED II strategy contract and writes a JSON provenance sidecar beside the output file

## Repository layout

```text
macro-strategy-conditioning/
|- README.md
|- requirements.txt
|- pyproject.toml
|- data/
|  |- macro/
|  `- strategies/
|- src/
|  |- data/
|  |- conditioning/
|  `- visualization/
|- notebooks/
`- tests/
```

## Core modules

- `src/data/validators.py`: schema and consistency checks.
- `src/data/loaders.py`: CSV loaders for macro and strategy inputs.
- `src/conditioning/regime_join.py`: strict date joins with no forward-looking merges.
- `src/conditioning/regime_stats.py`: descriptive return, drawdown, tail, and volatility summaries by regime.
- `src/conditioning/transition_analysis.py`: descriptive event windows and transition-aligned summaries around realized transitions.
- `src/conditioning/final_summary_report.py`: shared table builders for the final Notebook 08 research packet.
- `src/visualization/plots.py`: Plotly diagnostics for MVP notebooks.

## Notebook roadmap

Implemented notebooks are intentionally narrow and descriptive. The current completed sequence now runs through Notebook `08`.

1. `00_orientation.ipynb` - scope, constraints, and repository tour
2. `01_inputs_validation.ipynb` - implemented; validation gatekeeper for schema, coverage, and transition consistency
3. `02_returns_by_regime.ipynb` - implemented; first MVP analysis notebook for conditional return summaries after validation passes
4. `03_risk_drawdowns.ipynb` - implemented; descriptive risk and drawdown diagnostics by macro regime
5. `04_transition_behavior.ipynb` - implemented; descriptive behavior around historical macro regime transitions
6. `05_cross_strategy.ipynb` - implemented; real macro plus sample-strategy integration foundation and coverage boundary check
7. `06_regime_robustness.ipynb` - implemented; real macro integration overview plus regime-conditioned diagnostics and sparse-coverage warnings
8. `07_transition_diagnostics.ipynb` - implemented; transition coverage diagnostics and event-window alignment checks
9. `08_final_summary_packet.ipynb` - implemented; final descriptive research summary packet consolidating the 05-07 outputs

Notebook `08` is not an interactive dashboard. Any future dashboard work remains explicitly out of scope for the current research contract.

Execution note:
- notebooks now resolve the repository root and checked-in data paths automatically, so they can be launched from the `notebooks/` directory or executed headlessly without manual `PYTHONPATH` setup
- notebooks `01`-`04` remain the example-contract MVP path
- notebooks `05`-`08` are the canonical real Part I to Part II handoff workflow

## Example workflow

1. Place monthly macro files in `data/macro/`, preferably as `regimes.csv` and `transitions.csv`.
2. Place strategy return files in `data/strategies/`.
   If the source file comes from Alpha Generation Phase 2, first normalize it with `python scripts/export_alpha_generation_strategy_returns.py --input <alpha_generation_period_returns.csv> --output <fredii_strategy_returns.csv>`.
3. Load inputs via `src/data/loaders.py`.
4. Run `01_inputs_validation.ipynb` or `run_all_validations(...)` as the gatekeeper step.
5. Optionally run `python scripts/smoke_real_macro_contract.py` for a direct contract audit of the macro files, including any documented internal missing regime months.
6. Run `05_cross_strategy.ipynb` to establish the real-macro/sample-strategy integration baseline and confirm the overlap boundary.
7. Run `06_regime_robustness.ipynb` for descriptive real-macro diagnostics and sparse-sample regime coverage warnings.
8. Run `07_transition_diagnostics.ipynb` for transition alignment diagnostics and clean empty-state handling when no transition dates overlap strategy coverage.
9. Run `08_final_summary_packet.ipynb` for the final table-oriented research summary packet.
10. Interpret outputs as descriptive context only; they are not forecasts, signals, rankings, optimizations, allocations, or trading recommendations.

The implemented notebooks intentionally keep `data/strategies/strategy_returns_example.csv` as their default minimal contract fixture so the sparse-coverage and zero-aligned-transition behavior remains easy to reproduce.

If you want broader synthetic coverage for diagnostics or tests, swap `data/strategies/strategy_returns_wide_sample.csv` into the strategy loader path instead of the narrow example fixture.

Transition-event semantics:
- transition event windows use true calendar month offsets from each `transition_date`
- missing calendar months remain missing; they are not compressed into ordinal event time
- transition completeness diagnostics are built on the expected strategy-by-transition grid, so zero-observation strategy windows are reported as missing rather than silently omitted
- raw event-window diagnostics retain incomplete windows for inspection
- aggregate transition summaries in Notebooks `07` and `08` use only complete per-strategy windows and report incomplete-window counts separately

## 05-08 flow

The implemented 05-08 sequence is designed as a narrow descriptive research path:

- Notebook `05` establishes the real macro plus sample-strategy integration foundation and makes the overlap boundary explicit.
- Notebook `06` summarizes realized macro regime coverage within the current strategy window and flags sparse or missing regime observations as sample caveats.
- Notebook `07` checks transition alignment, reports incomplete per-strategy event windows explicitly, and limits aggregate transition summaries to complete per-strategy windows.
- Notebook `08` assembles a final research summary packet from shared table builders in `src/conditioning/final_summary_report.py`, preserving optional strategy metadata when present and leaving those fields blank when absent.

The narrow checked-in example strategy file is intentionally sparse, so the final packet may remain sparse and may show zero aligned transitions when that fixture is used. The wider synthetic sample fixture exists only to exercise broader descriptive regime and transition coverage; neither fixture is production data or a basis for portfolio or trading decisions.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Verified on August 17, 2026:
- `pytest` passed with 76 tests, including Alpha Generation adapter coverage and canonical macro-cadence regression checks
- `python scripts/smoke_real_macro_contract.py` passed on the checked-in real macro files plus the narrow strategy fixture
- `python scripts/smoke_real_macro_contract.py --regimes data/macro/regimes.csv --transitions data/macro/transitions.csv --strategy data/strategies/strategy_returns_wide_sample.csv` passed
- notebooks `00` through `08` executed successfully in headless validation after the repository-root bootstrap was added
- notebooks `05` through `08` were revalidated after the transition-window and minimum-strategy-contract fixes
- final real-data acceptance also passed against a 141-row Alpha Generation export spanning 3 strategies, with all 141 rows matching the refreshed macro handoff and the accepted 05-08 workflow reporting 6 aligned transitions, 56 transitions outside coverage, 18 strategy-transition windows, 15 complete windows, 3 partial windows, and 0 missing windows

Current real-macro cadence note:
- the canonical `data/macro/regimes.csv` file now spans `1991-01-31` through `2025-12-31` with no internal missing month-end dates
- `2025-10-31` is now present in the checked-in macro handoff, so strict exact-date joins accept real strategy rows normalized to that month-end without any forward- or backward-fill behavior

## Non-predictive disclaimer

All outputs are descriptive and historical. Any observed relationship between returns and macro labels should be interpreted as conditional context, **not** a forecast, **not** a trading recommendation, and **not** investment advice.
