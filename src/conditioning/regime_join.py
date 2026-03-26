"""Join strategy return streams to macro regimes with strict date matching."""

from __future__ import annotations

import pandas as pd


def join_returns_with_regimes(strategy_returns: pd.DataFrame, regimes: pd.DataFrame) -> pd.DataFrame:
    """Inner join strategy returns with regimes by exact DATE.

    This prevents forward-looking or as-of joins.
    """
    merged = strategy_returns.merge(regimes, on="DATE", how="inner", validate="many_to_one")

    missing_after_join = strategy_returns.loc[~strategy_returns["DATE"].isin(merged["DATE"])]
    if not missing_after_join.empty:
        raise ValueError("some strategy rows did not match macro DATE exactly; forward-looking joins are not allowed")

    return merged.sort_values(["strategy_id", "DATE"]).reset_index(drop=True)
