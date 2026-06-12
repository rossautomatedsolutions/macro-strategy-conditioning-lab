# MVP Data Contract Checkpoint

FRED II / Part II is at a clean MVP data-contract checkpoint.

- Notebooks `01` through `08` are implemented and reviewed.
- Real Part I macro files in `data/macro/` passed the Part II contract audit.
- `pytest` passed.
- The explicit real macro smoke check passed with:
  `python scripts\smoke_real_macro_contract.py --regimes data\macro\regimes.csv --transitions data\macro\transitions.csv`
- Notebook `08` is the final descriptive research summary packet, not an interactive dashboard.

Current remaining caveats:

- The narrow checked-in example strategy file has no overlap with the current macro transition dates, so transition coverage is reported as outside coverage rather than aligned.
- Zero aligned transitions is acceptable for the narrow checked-in example strategy window and is not a contract failure.
- The final summary packet can be sparse when the checked-in strategy sample window is narrow.
- A wider synthetic strategy sample fixture is also checked in to exercise broader descriptive regime coverage and aligned transition examples without implying real strategy performance.
- Strict hash comparison to the original OneDrive CSV exports remains optional future provenance work.
