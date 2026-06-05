# MVP Data Contract Checkpoint

FRED II / Part II is at a clean MVP data-contract checkpoint.

- Notebooks `01` through `04` are implemented and reviewed.
- Real Part I macro files in `data/macro/` passed the Part II contract audit.
- `pytest` passed.
- The explicit real macro smoke check passed with:
  `python scripts\smoke_real_macro_contract.py --regimes data\macro\regimes.csv --transitions data\macro\transitions.csv`
- Notebook `05` through `08` and the dashboard are deferred.

Current remaining caveats:

- The sample strategy file has no overlap with the current macro transition dates, so transition coverage is reported as outside coverage rather than aligned.
- Strict hash comparison to the original OneDrive CSV exports remains optional future provenance work.
