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


def build_sparse_regime_coverage_table(
    joined: pd.DataFrame,
    regimes: pd.DataFrame,
    sparse_threshold: int = 3,
) -> pd.DataFrame:
    """Return per-strategy regime coverage flags for sparse or missing samples."""
    macro_counts = build_macro_regime_category_counts(regimes).rename(columns={"count": "macro_months_available"})
    strategies = pd.DataFrame({"strategy_id": sorted(joined["strategy_id"].unique())})
    categories = macro_counts[["Macro_Regime"]].drop_duplicates().sort_values("Macro_Regime").reset_index(drop=True)
    coverage_grid = strategies.assign(_key=1).merge(categories.assign(_key=1), on="_key").drop(columns="_key")

    strategy_obs = (
        joined.groupby(["strategy_id", "Macro_Regime"])
        .size()
        .reset_index(name="strategy_obs")
    )

    coverage = coverage_grid.merge(strategy_obs, on=["strategy_id", "Macro_Regime"], how="left")
    coverage = coverage.merge(macro_counts, on="Macro_Regime", how="left", validate="many_to_one")
    coverage["strategy_obs"] = coverage["strategy_obs"].fillna(0).astype(int)

    coverage["coverage_status"] = "adequate"
    coverage.loc[coverage["strategy_obs"] == 0, "coverage_status"] = "unobserved"
    coverage.loc[
        (coverage["strategy_obs"] > 0) & (coverage["strategy_obs"] < sparse_threshold),
        "coverage_status",
    ] = "sparse"
    coverage["sample_caveat"] = (
        "Diagnostic warning only; not a trading conclusion."
    )
    return coverage.sort_values(["strategy_id", "Macro_Regime"]).reset_index(drop=True)
