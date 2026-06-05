"""Conditional diagnostics of strategy returns by macro regime."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_cumulative_returns(returns: pd.Series) -> pd.Series:
    """Compute cumulative return path from a monthly return series."""
    return (1 + pd.Series(returns, copy=True)).cumprod()


def compute_drawdown_series(returns: pd.Series) -> pd.Series:
    """Compute drawdown series from a monthly return series."""
    cumulative = compute_cumulative_returns(returns)
    running_peak = cumulative.cummax()
    return (cumulative / running_peak) - 1


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
    """Compute descriptive drawdown diagnostics by strategy and regime."""
    out_rows: list[dict] = []

    for (strategy_id, regime), grp in df.groupby(["strategy_id", regime_col]):
        ordered = grp.sort_values("DATE")
        drawdown = compute_drawdown_series(ordered["returns"])
        out_rows.append(
            {
                "strategy_id": strategy_id,
                regime_col: regime,
                "max_drawdown": float(drawdown.min()),
                "average_drawdown": float(drawdown.mean()),
                "obs": len(ordered),
            }
        )

    return pd.DataFrame(out_rows)


def risk_summary_by_regime(df: pd.DataFrame, regime_col: str = "Macro_Regime") -> pd.DataFrame:
    """Compute descriptive risk summaries by strategy and regime."""
    grouped = df.groupby(["strategy_id", regime_col])["returns"]
    out = grouped.agg(
        volatility="std",
        worst_monthly_return="min",
        tail_return_5pct=lambda s: s.quantile(0.05),
        obs="count",
    ).reset_index()

    drawdown = drawdown_by_regime(df, regime_col=regime_col)
    return out.merge(drawdown, on=["strategy_id", regime_col, "obs"], how="left", validate="one_to_one")
