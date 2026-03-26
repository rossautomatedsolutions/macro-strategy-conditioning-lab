"""I/O helpers for macro regime and strategy return datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATE_COL = "DATE"
TRANSITION_DATE_COL = "transition_date"


def _coerce_datetime(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Return a copy of *df* with *col* parsed to datetime."""
    out = df.copy()
    out[col] = pd.to_datetime(out[col])
    return out


def load_regimes(path: str | Path) -> pd.DataFrame:
    """Load monthly macro regime table with required schema from CSV."""
    df = pd.read_csv(path)
    return _coerce_datetime(df, DATE_COL).sort_values(DATE_COL).reset_index(drop=True)


def load_transitions(path: str | Path) -> pd.DataFrame:
    """Load regime transition events from CSV."""
    df = pd.read_csv(path)
    return _coerce_datetime(df, TRANSITION_DATE_COL).sort_values(TRANSITION_DATE_COL).reset_index(drop=True)


def load_strategy_returns(path: str | Path) -> pd.DataFrame:
    """Load strategy monthly return table from CSV."""
    df = pd.read_csv(path)
    return _coerce_datetime(df, DATE_COL).sort_values(["strategy_id", DATE_COL]).reset_index(drop=True)
