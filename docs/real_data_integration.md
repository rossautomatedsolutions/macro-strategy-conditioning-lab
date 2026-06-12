# Real Data Integration

This repository consumes realized Part I macro outputs as a locked data contract.

## Current provenance note

The current real macro files in `data/macro/` were exported/reconstructed from executed Part I notebook payloads.

The original standalone OneDrive CSV exports were not available in this workspace during the handoff.

Strict source-file hash comparison against those original standalone exports remains optional future provenance work.

## Expected macro file locations

Place upstream Part I files in `data/macro/`. The default expected filenames are:

- `data/macro/regimes.csv`
- `data/macro/transitions.csv`

If those files are not present, the smoke script falls back to:

- `data/macro/regimes_example.csv`
- `data/macro/transitions_example.csv`

Strategy returns are still allowed to use checked-in synthetic/sample-only files during this audit phase:

- `data/strategies/strategy_returns_example.csv`
- `data/strategies/strategy_returns_wide_sample.csv`

The narrow file preserves the sparse-coverage and zero-aligned-transition contract examples. The wider file exists only to exercise broader descriptive regime coverage and aligned transition diagnostics.

The current notebook examples and the default smoke-script behavior intentionally stay on the narrow fixture. Use the wide fixture only when you want richer synthetic descriptive coverage.

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

Zero aligned transitions is acceptable for the narrow checked-in example strategy window. That outcome reflects limited overlap, not a macro schema failure.

Sparse regime coverage in later notebook outputs is also acceptable when the sample strategy history is narrow. Those warnings are descriptive sample caveats, not trading conclusions.

## Implemented 05-08 research flow

- `notebooks/05_cross_strategy.ipynb` establishes the real macro plus sample-strategy integration baseline.
- `notebooks/06_regime_robustness.ipynb` summarizes realized regime coverage and sparse-sample diagnostics.
- `notebooks/07_transition_diagnostics.ipynb` checks transition alignment and event-window eligibility.
- `notebooks/08_final_summary_packet.ipynb` assembles the final descriptive research summary packet.

This flow remains descriptive research infrastructure only. It does not implement forecasting, signals, ranking, optimization, allocation, recommendation, trading, or an interactive dashboard.

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

Optional wide synthetic fixture path:

```powershell
python scripts/smoke_real_macro_contract.py --regimes data/macro/regimes.csv --transitions data/macro/transitions.csv --strategy data/strategies/strategy_returns_wide_sample.csv
```

The smoke script prints:

- regime row count
- transition row count
- macro date range
- number of `Macro_Regime` categories
- transition rows aligned to strategy coverage
- transition rows outside strategy coverage

It exits nonzero only on real contract failures.
