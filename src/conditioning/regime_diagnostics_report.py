"""Reusable table builders for Notebook 06 regime-conditioned diagnostics."""

from __future__ import annotations

import pandas as pd

from src.conditioning.regime_join import join_returns_with_regimes
from src.conditioning.regime_stats import regime_diagnostics_by_regime
from src.data.integration_summary import (
    build_real_macro_integration_overview,
    build_sparse_regime_coverage_table,
)


def build_macro_regime_observation_summary(joined: pd.DataFrame) -> pd.DataFrame:
    """Return simple realized coverage and return dispersion by macro regime."""
    summary = (
        joined.groupby("Macro_Regime")
        .agg(
            observation_count=("returns", "size"),
            strategy_count=("strategy_id", "nunique"),
            average_return=("returns", "mean"),
            volatility=("returns", "std"),
            min_return=("returns", "min"),
            max_return=("returns", "max"),
        )
        .reset_index()
    )
    return summary.sort_values(["observation_count", "Macro_Regime"], ascending=[False, True]).reset_index(drop=True)


def build_notebook_06_tables(
    regimes: pd.DataFrame,
    transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
    *,
    sparse_threshold: int = 3,
) -> dict[str, pd.DataFrame]:
    """Assemble the descriptive tables displayed by Notebook 06."""
    integration_overview, coverage = build_real_macro_integration_overview(
        regimes,
        transitions,
        strategy_returns,
    )
    joined = join_returns_with_regimes(strategy_returns, regimes)
    sparse_coverage = build_sparse_regime_coverage_table(joined, regimes, sparse_threshold=sparse_threshold)
    sparse_warnings = sparse_coverage.loc[sparse_coverage["coverage_status"] != "adequate"].reset_index(drop=True)

    transition_coverage_summary = pd.DataFrame(
        [
            {
                "transitions_inside_strategy_coverage": len(coverage.aligned),
                "transitions_outside_strategy_coverage": len(coverage.outside_coverage),
            }
        ]
    )

    return {
        "integration_overview": integration_overview,
        "transition_coverage_summary": transition_coverage_summary,
        "joined_preview": joined.loc[:, ["DATE", "strategy_id", "returns", "Macro_Regime"]]
        .sort_values(["strategy_id", "DATE"])
        .reset_index(drop=True),
        "macro_regime_observation_summary": build_macro_regime_observation_summary(joined),
        "strategy_regime_diagnostics": regime_diagnostics_by_regime(joined),
        "sparse_coverage": sparse_coverage,
        "sparse_warnings": sparse_warnings,
    }
