# Real Data Integration

This repository consumes realized Part I macro outputs as a locked data contract.

## Current provenance note

The current real macro files in `data/macro/` were refreshed on August 17, 2026 after the upstream Part I October 2025 transformation fix.

The historical raw monthly source referenced by the executed Part I notebooks is `C:\Users\JR\OneDrive\Mini PC\FRED\data\raw\fred_monthly.csv`.

That original OneDrive path was identifiable from notebook evidence but not directly readable from this workspace, so the refreshed handoff was rebuilt from the fixed Part I logic plus executed upstream notebook evidence for the recovered October 2025 row.

The refreshed canonical regime table now includes `2025-10-31` as `Expansion / Inflationary / Easing`, and the transition table is otherwise unchanged versus the prior handoff.

Strict source-file hash comparison against the original standalone OneDrive exports remains optional future provenance work.

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

Only `DATE`, `strategy_id`, and `returns` are required for strategy inputs. If optional metadata such as `strategy_name`, `strategy_category`, or `asset_class` is absent, the final packet leaves those fields blank instead of treating the file as invalid.

The strategy contract is calendar month-end based. If an upstream research artifact keys monthly returns to the last available trading date of the month instead, normalize that date to calendar month-end before running FRED II.

## Alpha Generation adapter workflow

Alpha Generation Phase 2 `period_returns.csv` artifacts are not FRED II-native as written:

- `entry_date` is the last available trading date in the month, not always the literal calendar month-end
- `variant_id` is the strategy identifier
- `portfolio_return` is the monthly forward return for that executed strategy period

Use the explicit adapter:

```powershell
python scripts/export_alpha_generation_strategy_returns.py --input <alpha_generation_period_returns.csv> --output <fredii_strategy_returns.csv>
```

The adapter:

- validates required Alpha Generation source columns
- normalizes `entry_date` to calendar month-end for FRED II `DATE`
- maps `variant_id -> strategy_id`
- maps `portfolio_return -> returns`
- carries `variant_name -> strategy_name` when present
- fails if month-end normalization would create duplicate `DATE/strategy_id` rows
- fails on malformed or non-finite returns
- writes a JSON provenance sidecar beside the exported CSV

This utility is intentionally an ingestion step only. The 05-08 notebooks do not depend on the Alpha Generation repository.

The implemented notebooks now resolve the repository root and checked-in data paths automatically, so the 05-08 sequence can be executed from the `notebooks/` directory or via headless notebook execution without manual path edits.

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
- every transition `from` and `to` value must also match the realized regime sequence at that `transition_date`
- strategy `returns` must be finite numeric values

Transition rows outside the available strategy coverage are reported separately. They are not a contract failure during this Part II audit.

Strategy rows on `2025-10-31` now pass the exact-date contract against the checked-in canonical macro handoff.

Zero aligned transitions is acceptable for the narrow checked-in example strategy window. That outcome reflects limited overlap, not a macro schema failure.

Sparse regime coverage in later notebook outputs is also acceptable when the sample strategy history is narrow. Those warnings are descriptive sample caveats, not trading conclusions.

Transition event windows in Notebooks `07` and `08` use true calendar month offsets from each transition month. Missing calendar months remain missing rather than being collapsed into ordinal event time. Transition completeness diagnostics are built on the expected strategy-by-transition grid, so strategies with zero observations anywhere in an aligned event window are reported as missing rather than silently omitted. Aggregate transition summaries use only complete per-strategy windows, while incomplete windows are retained and reported separately for diagnostics.

## Implemented 05-08 research flow

- `notebooks/05_cross_strategy.ipynb` establishes the real macro plus sample-strategy integration baseline.
- `notebooks/06_regime_robustness.ipynb` summarizes realized regime coverage and sparse-sample diagnostics.
- `notebooks/07_transition_diagnostics.ipynb` checks transition alignment, event-window completeness, and explicit zero-observation strategy windows before showing complete-window-only transition aggregates.
- `notebooks/08_final_summary_packet.ipynb` assembles the final descriptive research summary packet and carries forward the transition completeness caveats.

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

The smoke script now also prints whether the canonical macro range contains any internal missing month-end dates.

Optional explicit paths:

```powershell
python scripts/smoke_real_macro_contract.py --regimes data/macro/regimes.csv --transitions data/macro/transitions.csv --strategy data/strategies/strategy_returns_example.csv
```

Optional wide synthetic fixture path:

```powershell
python scripts/smoke_real_macro_contract.py --regimes data/macro/regimes.csv --transitions data/macro/transitions.csv --strategy data/strategies/strategy_returns_wide_sample.csv
```

As of August 17, 2026, the canonical 05-08 notebook path and both smoke-check commands were revalidated successfully against the checked-in repository state. That revalidation also confirmed that Notebook `08` now works with a required-only strategy input containing just `DATE`, `strategy_id`, and `returns`, that uneven strategy calendars surface as explicit missing transition windows rather than silent omissions, and that the checked-in macro handoff now has complete month-end coverage through `2025-12-31`, including `2025-10-31`.

The smoke script prints:

- regime row count
- transition row count
- macro date range
- number of `Macro_Regime` categories
- transition rows aligned to strategy coverage
- transition rows outside strategy coverage

It exits nonzero only on real contract failures.
