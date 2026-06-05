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

## Repository layout

```text
macro-strategy-conditioning/
├── README.md
├── requirements.txt
├── pyproject.toml
├── data/
│   ├── macro/
│   └── strategies/
├── src/
│   ├── data/
│   ├── conditioning/
│   └── visualization/
├── notebooks/
└── tests/
```

## Core modules

- `src/data/validators.py`: schema and consistency checks.
- `src/data/loaders.py`: CSV loaders for macro and strategy inputs.
- `src/conditioning/regime_join.py`: strict date joins with no forward-looking merges.
- `src/conditioning/regime_stats.py`: descriptive return, drawdown, tail, and volatility summaries by regime.
- `src/conditioning/transition_analysis.py`: descriptive event windows and transition-aligned summaries around realized transitions.
- `src/visualization/plots.py`: Plotly diagnostics for MVP notebooks.

## Notebook roadmap

Implemented notebooks are intentionally narrow. Planned notebooks remain placeholders until their responsibilities are actually built.

1. `00_orientation.ipynb` — scope, constraints, and repository tour
2. `01_inputs_validation.ipynb` — implemented; validation gatekeeper for schema, coverage, and transition consistency
3. `02_returns_by_regime.ipynb` — implemented; first MVP analysis notebook for conditional return summaries after validation passes
4. `03_risk_drawdowns.ipynb` — implemented; descriptive risk and drawdown diagnostics by macro regime
5. `04_transition_behavior.ipynb` — implemented; descriptive behavior around historical macro regime transitions
6. `05_cross_strategy.ipynb` — planned/future
7. `06_regime_robustness.ipynb` — planned/future
8. `07_interpretation.ipynb` — planned/future
9. `08_dashboard.ipynb` — deferred; not part of the current MVP

## Example workflow

1. Place monthly macro files in `data/macro/`, preferably as `regimes.csv` and `transitions.csv`.
2. Place strategy return files in `data/strategies/`.
3. Load inputs via `src/data/loaders.py`.
4. Run `01_inputs_validation.ipynb` or `run_all_validations(...)` as the gatekeeper step.
5. Optionally run `python scripts/smoke_real_macro_contract.py` for a direct contract audit of the macro files.
6. Run `02_returns_by_regime.ipynb` for the first MVP analysis.
7. Run `03_risk_drawdowns.ipynb` for descriptive risk and drawdown diagnostics.
8. Run `04_transition_behavior.ipynb` for descriptive transition-aligned context analysis.
9. Join returns with regimes by exact `DATE`.
10. Compute conditional stats and visualize descriptive diagnostics.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Non-predictive disclaimer

All outputs are descriptive and historical. Any observed relationship between returns and macro labels should be interpreted as conditional context, **not** a forecast and **not** a trading recommendation.
