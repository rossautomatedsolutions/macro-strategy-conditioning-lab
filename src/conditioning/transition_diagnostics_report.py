"""Reusable table builders for Notebook 07 transition-event diagnostics."""

from __future__ import annotations

import pandas as pd

from src.conditioning.regime_join import join_returns_with_regimes
from src.conditioning.transition_analysis import (
    build_transition_windows,
    cumulative_transition_profile,
    summarize_transition_windows,
)
from src.data.integration_summary import build_real_macro_integration_overview


def build_transition_coverage_summary(
    transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
    aligned_transitions: pd.DataFrame,
    outside_coverage_transitions: pd.DataFrame,
) -> pd.DataFrame:
    """Return a one-row transition coverage summary for Notebook 07."""
    return pd.DataFrame(
        [
            {
                "total_transition_rows": len(transitions),
                "transitions_inside_strategy_coverage": len(aligned_transitions),
                "transitions_outside_strategy_coverage": len(outside_coverage_transitions),
                "earliest_transition_date": transitions["transition_date"].min(),
                "latest_transition_date": transitions["transition_date"].max(),
                "strategy_start": strategy_returns["DATE"].min(),
                "strategy_end": strategy_returns["DATE"].max(),
            }
        ]
    )


def build_transition_window_status(aligned_transitions: pd.DataFrame) -> pd.DataFrame:
    """Return a compact status table for aligned transition event windows."""
    if aligned_transitions.empty:
        return pd.DataFrame(
            [
                {
                    "status": "empty",
                    "aligned_transition_count": 0,
                    "message": (
                        "No transition dates overlap the current sample strategy window; "
                        "this is acceptable for the checked-in sample file and not a contract failure."
                    ),
                }
            ]
        )

    return pd.DataFrame(
        [
            {
                "status": "ok",
                "aligned_transition_count": len(aligned_transitions),
                "message": "Aligned transition dates are available for descriptive event-window diagnostics.",
            }
        ]
    )


def build_notebook_07_tables(
    regimes: pd.DataFrame,
    transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
    *,
    window: int = 3,
) -> dict[str, pd.DataFrame]:
    """Assemble the descriptive tables displayed by Notebook 07."""
    integration_overview, coverage = build_real_macro_integration_overview(
        regimes,
        transitions,
        strategy_returns,
    )
    joined = join_returns_with_regimes(strategy_returns, regimes)
    transition_windows = build_transition_windows(joined, coverage.aligned, window=window)

    return {
        "integration_overview": integration_overview,
        "transition_coverage_summary": build_transition_coverage_summary(
            transitions,
            strategy_returns,
            coverage.aligned,
            coverage.outside_coverage,
        ),
        "aligned_transitions": coverage.aligned.reset_index(drop=True),
        "outside_coverage_transitions": coverage.outside_coverage.reset_index(drop=True),
        "transition_window_status": build_transition_window_status(coverage.aligned),
        "transition_windows": transition_windows,
        "transition_window_summary": summarize_transition_windows(transition_windows),
        "transition_cumulative_profile": cumulative_transition_profile(transition_windows),
    }
