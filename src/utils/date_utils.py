"""Date helpers for month-end normalization."""

from __future__ import annotations

import pandas as pd


def to_month_end(date_like: pd.Series | list | pd.Index) -> pd.Series:
    """Convert date-like values to normalized month-end timestamps."""
    dates = pd.to_datetime(date_like)
    return dates + pd.offsets.MonthEnd(0)
