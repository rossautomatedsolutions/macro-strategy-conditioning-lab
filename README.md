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

This repository consumes monthly macro outputs already prepared upstream:

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
│   ├── visualization/
│   └── utils/
├── notebooks/
└── tests/
```

## Core modules

- `src/data/validators.py`: schema and consistency checks.
- `src/conditioning/regime_join.py`: strict date joins (no forward-looking merges).
- `src/conditioning/regime_stats.py`: returns, volatility, and drawdown by regime.
- `src/conditioning/transition_analysis.py`: ±N month event windows around transitions.
- `src/visualization/plots.py`: Plotly diagnostics (distributions, drawdowns, transition profiles).

## Notebook roadmap

Each notebook answers one question and includes interpretation notes and non-predictive warnings.

1. `00_orientation.ipynb` — scope, constraints, and repository tour
2. `01_inputs_validation.ipynb` — verify schema and alignment quality
3. `02_returns_by_regime.ipynb` — conditional return summaries
4. `03_risk_drawdowns.ipynb` — regime-aware volatility and drawdowns
5. `04_transition_behavior.ipynb` — event-window behavior around transitions
6. `05_cross_strategy.ipynb` — cross-strategy comparative diagnostics
7. `06_regime_robustness.ipynb` — robustness checks across sub-periods
8. `07_interpretation.ipynb` — interpretation framework and caveats
9. `08_dashboard.ipynb` — assembled visual diagnostic dashboard

## Example workflow

1. Place monthly macro files in `data/macro/`.
2. Place strategy return files in `data/strategies/`.
3. Load inputs via `src/data/loaders.py`.
4. Run `run_all_validations(...)`.
5. Join returns with regimes by exact `DATE`.
6. Compute conditional stats and transition-window summaries.
7. Visualize diagnostics in notebooks.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Non-predictive disclaimer

All outputs are descriptive and historical. Any observed relationship between returns and macro labels should be interpreted as conditional context, **not** a forecast and **not** a trading recommendation.
