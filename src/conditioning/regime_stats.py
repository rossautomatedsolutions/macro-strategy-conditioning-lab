"""Conditional diagnostics of strategy returns by macro regime."""

from __future__ import annotations

import numpy as np
import pandas as pd


def returns_by_regime(df: pd.DataFrame, regime_col: str = "Macro_Regime") -> pd.DataFrame:
    """Compute mean, median, and hit-rate of returns per strategy and regime."""
    grouped = df.groupby(["strategy_id", regime_col])["returns"]
    out = grouped.agg(mean_return="mean", median_return="median", obs="count")
    out["hit_rate"] = grouped.apply(lambda s: (s > 0).mean())
    return out.reset_index()


def volatility_by_regime(df: pd.DataFrame, regime_col: str = "Macro_Regime") -> pd.DataFrame:
    """Compute standard deviation and downside deviation of returns per regime."""
    def downside_std(x: pd.Series) -> float:
        downside = x[x < 0]
        return float(downside.std(ddof=1)) if len(downside) > 1 else np.nan

    grouped = df.groupby(["strategy_id", regime_col])["returns"]
    out = grouped.agg(volatility="std", obs="count")
    out["downside_volatility"] = grouped.apply(downside_std)
    return out.reset_index()


def drawdown_by_regime(df: pd.DataFrame, regime_col: str = "Macro_Regime") -> pd.DataFrame:
    """Compute max drawdown measured within each regime block for each strategy."""
    out_rows: list[dict] = []

    for (strategy_id, regime), grp in df.groupby(["strategy_id", regime_col]):
        cum = (1 + grp.sort_values("DATE")["returns"]).cumprod()
        running_peak = cum.cummax()
        dd = (cum / running_peak) - 1
        out_rows.append(
            {
                "strategy_id": strategy_id,
                regime_col: regime,
                "max_drawdown": float(dd.min()),
                "obs": len(grp),
            }
        )

    return pd.DataFrame(out_rows)
