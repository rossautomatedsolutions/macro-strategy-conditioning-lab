# Real Data Integration

This repository consumes realized Part I macro outputs as a locked data contract.

## Expected macro file locations

Place upstream Part I files in `data/macro/`. The default expected filenames are:

- `data/macro/regimes.csv`
- `data/macro/transitions.csv`

If those files are not present, the smoke script falls back to:

- `data/macro/regimes_example.csv`
- `data/macro/transitions_example.csv`

Strategy returns are still allowed to use the sample file during this audit phase:

- `data/strategies/strategy_returns_example.csv`

## Required schemas

### Regimes

- `DATE`
- `Growth_Regime`
- `Inflation_Regime`
- `Policy_Regime`
- `Macro_Regime`

### Transitions

- `transition_date`
- `from`
- `to`

## Required contract rules

- `DATE` must be month-end
- `transition_date` must be month-end
- `Macro_Regime` must equal `"<Growth_Regime> / <Inflation_Regime> / <Policy_Regime>"`
- every `transition_date` must exist in `regimes.DATE`
- every transition `from` and `to` value must exist in `regimes.Macro_Regime`

Transition rows outside the available strategy coverage are reported separately. They are not a contract failure during this Part II audit.

## Validation paths

Run the full test suite:

```powershell
pytest
```

Run the direct macro contract smoke check:

```powershell
python scripts/smoke_real_macro_contract.py
```

Optional explicit paths:

```powershell
python scripts/smoke_real_macro_contract.py --regimes data/macro/regimes.csv --transitions data/macro/transitions.csv --strategy data/strategies/strategy_returns_example.csv
```

The smoke script prints:

- regime row count
- transition row count
- macro date range
- number of `Macro_Regime` categories
- transition rows aligned to strategy coverage
- transition rows outside strategy coverage

It exits nonzero only on real contract failures.
