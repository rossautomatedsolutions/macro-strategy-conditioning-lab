"""Reusable summary helpers for real macro/strategy integration examples."""

from __future__ import annotations

import pandas as pd

from src.data.validators import TransitionCoverageReport, audit_transition_coverage


def build_real_macro_integration_overview(
    regimes: pd.DataFrame,
    transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
) -> tuple[pd.DataFrame, TransitionCoverageReport]:
    """Return a one-row overview table plus transition coverage split."""
    coverage = audit_transition_coverage(transitions, strategy_returns)

    overlap_start = max(regimes["DATE"].min(), strategy_returns["DATE"].min())
    overlap_end = min(regimes["DATE"].max(), strategy_returns["DATE"].max())
    if overlap_start > overlap_end:
        overlap_start = pd.NaT
        overlap_end = pd.NaT

    overview = pd.DataFrame(
        [
            {
                "macro_row_count": len(regimes),
                "transition_row_count": len(transitions),
                "strategy_row_count": len(strategy_returns),
                "macro_start": regimes["DATE"].min(),
                "macro_end": regimes["DATE"].max(),
                "strategy_start": strategy_returns["DATE"].min(),
                "strategy_end": strategy_returns["DATE"].max(),
                "overlap_start": overlap_start,
                "overlap_end": overlap_end,
                "macro_regime_categories": regimes["Macro_Regime"].nunique(),
                "transitions_inside_strategy_coverage": len(coverage.aligned),
                "transitions_outside_strategy_coverage": len(coverage.outside_coverage),
            }
        ]
    )
    return overview, coverage


def build_macro_regime_category_counts(regimes: pd.DataFrame) -> pd.DataFrame:
    """Return simple frequency counts for realized macro regime labels."""
    return (
        regimes["Macro_Regime"]
        .value_counts(dropna=False)
        .rename_axis("Macro_Regime")
        .reset_index(name="count")
        .sort_values(["count", "Macro_Regime"], ascending=[False, True])
        .reset_index(drop=True)
    )
