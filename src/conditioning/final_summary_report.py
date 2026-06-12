"""Reusable table builders for Notebook 08 final research summary packet."""

from __future__ import annotations

import pandas as pd

from src.conditioning.regime_diagnostics_report import build_notebook_06_tables
from src.conditioning.transition_diagnostics_report import build_notebook_07_tables
from src.data.integration_summary import (
    build_macro_regime_category_counts,
    build_real_macro_integration_overview,
)


def build_strategy_coverage_summary(strategy_returns: pd.DataFrame) -> pd.DataFrame:
    """Return compact coverage metadata for the sample strategy file."""
    return (
        strategy_returns.groupby("strategy_id")
        .agg(
            strategy_name=("strategy_name", "first"),
            strategy_category=("strategy_category", "first"),
            asset_class=("asset_class", "first"),
            observation_count=("returns", "size"),
            strategy_start=("DATE", "min"),
            strategy_end=("DATE", "max"),
        )
        .reset_index()
        .sort_values("strategy_id")
        .reset_index(drop=True)
    )


def build_overlap_summary(integration_overview: pd.DataFrame) -> pd.DataFrame:
    """Return a narrow overlap-focused slice from the shared integration overview."""
    columns = [
        "macro_start",
        "macro_end",
        "strategy_start",
        "strategy_end",
        "overlap_start",
        "overlap_end",
        "transitions_inside_strategy_coverage",
        "transitions_outside_strategy_coverage",
    ]
    return integration_overview.loc[:, columns].reset_index(drop=True)


def build_aligned_skipped_transition_summary(
    aligned_transitions: pd.DataFrame,
    outside_coverage_transitions: pd.DataFrame,
) -> pd.DataFrame:
    """Return a compact count summary for aligned versus skipped transitions."""
    return pd.DataFrame(
        [
            {
                "aligned_transition_rows": len(aligned_transitions),
                "skipped_transition_rows": len(outside_coverage_transitions),
            }
        ]
    )


def build_caveats_table(
    strategy_returns: pd.DataFrame,
    realized_macro_regime_counts: pd.DataFrame,
    aligned_transitions: pd.DataFrame,
) -> pd.DataFrame:
    """Return packet caveats as a compact table."""
    strategy_start = strategy_returns["DATE"].min().date()
    strategy_end = strategy_returns["DATE"].max().date()
    realized_category_count = realized_macro_regime_counts["Macro_Regime"].nunique()
    aligned_count = len(aligned_transitions)

    if aligned_count == 0:
        transition_detail = (
            "Zero aligned transition rows is acceptable for the current synthetic/sample input "
            "and is not a contract failure."
        )
    else:
        transition_detail = (
            f"The current synthetic/sample input includes {aligned_count} aligned transition rows "
            "for descriptive transition diagnostics."
        )

    return pd.DataFrame(
        [
            {
                "caveat": "sample_strategy_window",
                "detail": (
                    "The checked-in strategy fixtures are synthetic/sample-only. "
                    f"The current input spans {strategy_start} through {strategy_end}."
                ),
            },
            {
                "caveat": "realized_regime_coverage",
                "detail": (
                    f"The current input observes {realized_category_count} realized Macro_Regime "
                    "categories inside its strategy window."
                ),
            },
            {
                "caveat": "transition_alignment_context",
                "detail": transition_detail,
            },
            {
                "caveat": "research_only",
                "detail": "This notebook is descriptive research infrastructure only and is not a trading model or investment advice.",
            },
        ]
    )


def build_deferred_work_table() -> pd.DataFrame:
    """Return explicit follow-up items that remain out of scope for Notebook 08."""
    return pd.DataFrame(
        [
            {
                "deferred_work": "broader_strategy_history",
                "detail": "Use a wider strategy return history to increase realized regime and transition coverage in later research.",
            },
            {
                "deferred_work": "additional_sample_strategies",
                "detail": "Add more sample strategies only when needed for broader descriptive coverage; keep methodology unchanged.",
            },
            {
                "deferred_work": "dashboarding_out_of_scope",
                "detail": "Interactive dashboards remain out of scope for this notebook and should not be inferred from this packet.",
            },
        ]
    )


def build_notebook_08_tables(
    regimes: pd.DataFrame,
    transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
    *,
    sparse_threshold: int = 3,
    window: int = 3,
) -> dict[str, pd.DataFrame]:
    """Assemble the final table-oriented research summary packet for Notebook 08."""
    integration_overview, _ = build_real_macro_integration_overview(
        regimes,
        transitions,
        strategy_returns,
    )
    notebook_06 = build_notebook_06_tables(
        regimes,
        transitions,
        strategy_returns,
        sparse_threshold=sparse_threshold,
    )
    notebook_07 = build_notebook_07_tables(
        regimes,
        transitions,
        strategy_returns,
        window=window,
    )

    return {
        "input_coverage_summary": integration_overview,
        "macro_regime_file_summary": build_macro_regime_category_counts(regimes),
        "strategy_coverage_summary": build_strategy_coverage_summary(strategy_returns),
        "overlap_summary": build_overlap_summary(integration_overview),
        "realized_macro_regime_category_counts": notebook_06["macro_regime_observation_summary"],
        "regime_diagnostics_summary": notebook_06["strategy_regime_diagnostics"],
        "sparse_missing_regime_warnings": notebook_06["sparse_warnings"],
        "transition_coverage_summary": notebook_07["transition_coverage_summary"],
        "aligned_skipped_transition_summary": build_aligned_skipped_transition_summary(
            notebook_07["aligned_transitions"],
            notebook_07["outside_coverage_transitions"],
        ),
        "aligned_transition_rows": notebook_07["aligned_transitions"],
        "skipped_transition_rows": notebook_07["outside_coverage_transitions"],
        "caveats": build_caveats_table(
            strategy_returns,
            notebook_06["macro_regime_observation_summary"],
            notebook_07["aligned_transitions"],
        ),
        "deferred_work": build_deferred_work_table(),
    }
