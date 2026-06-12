# macro-strategy-conditioning

A research repository for diagnosing how **strategy return series** behave under different **macro regimes**.

> **Important:** This project is **not** a trading system, **not** a signal engine, and **not** a forecasting model. It is strictly a descriptive, conditional analysis framework.

## Purpose

`macro-strategy-conditioning` helps answer questions like:
- How do strategy returns differ across observed macro regimes?
- How does volatility or drawdown change by regime label?
- What behavior appears around realized macro transition dates?

The goal is interpretation and robustness diagnostics, not prediction.

## Relationship to Part I (Macro Interface)

This repository consumes monthly macro outputs already prepared upstream.

For direct real-data placement and smoke-check instructions, see [docs/real_data_integration.md](/C:/GitHub/macro-strategy-conditioning-lab/docs/real_data_integration.md).

Current provenance note:
- the checked-in `data/macro/regimes.csv` and `data/macro/transitions.csv` files were exported/reconstructed from executed Part I notebook payloads
- the original standalone OneDrive CSV exports were not available in the workspace during handoff
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

Rules respected in this repo:
- strategies are treated as black-box return streams
- no positions, no execution logic
- no optimization routines

Checked-in strategy fixtures:
- `data/strategies/strategy_returns_example.csv`: narrow synthetic/sample-only fixture used to preserve sparse-coverage and zero-aligned-transition examples
- `data/strategies/strategy_returns_wide_sample.csv`: wider synthetic/sample-only fixture used to exercise broader descriptive regime coverage and aligned transition examples

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

## Example workflow

1. Place monthly macro files in `data/macro/`, preferably as `regimes.csv` and `transitions.csv`.
2. Place strategy return files in `data/strategies/`.
3. Load inputs via `src/data/loaders.py`.
4. Run `01_inputs_validation.ipynb` or `run_all_validations(...)` as the gatekeeper step.
5. Optionally run `python scripts/smoke_real_macro_contract.py` for a direct contract audit of the macro files.
6. Run `05_cross_strategy.ipynb` to establish the real-macro/sample-strategy integration baseline and confirm the overlap boundary.
7. Run `06_regime_robustness.ipynb` for descriptive real-macro diagnostics and sparse-sample regime coverage warnings.
8. Run `07_transition_diagnostics.ipynb` for transition alignment diagnostics and clean empty-state handling when no transition dates overlap strategy coverage.
9. Run `08_final_summary_packet.ipynb` for the final table-oriented research summary packet.
10. Interpret outputs as descriptive context only; they are not forecasts, signals, rankings, optimizations, allocations, or trading recommendations.

The implemented notebooks intentionally keep `data/strategies/strategy_returns_example.csv` as their default minimal contract fixture so the sparse-coverage and zero-aligned-transition behavior remains easy to reproduce.

If you want broader synthetic coverage for diagnostics or tests, swap `data/strategies/strategy_returns_wide_sample.csv` into the strategy loader path instead of the narrow example fixture.

## 05-08 flow

The implemented 05-08 sequence is designed as a narrow descriptive research path:

- Notebook `05` establishes the real macro plus sample-strategy integration foundation and makes the overlap boundary explicit.
- Notebook `06` summarizes realized macro regime coverage within the current strategy window and flags sparse or missing regime observations as sample caveats.
- Notebook `07` checks transition alignment and treats zero aligned transitions as an acceptable sample-window outcome rather than a contract failure.
- Notebook `08` assembles a final research summary packet from shared table builders in `src/conditioning/final_summary_report.py`.

The narrow checked-in example strategy file is intentionally sparse, so the final packet may remain sparse and may show zero aligned transitions when that fixture is used. The wider synthetic sample fixture exists only to exercise broader descriptive regime and transition coverage; neither fixture is production data or a basis for portfolio or trading decisions.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Non-predictive disclaimer

All outputs are descriptive and historical. Any observed relationship between returns and macro labels should be interpreted as conditional context, **not** a forecast, **not** a trading recommendation, and **not** investment advice.
