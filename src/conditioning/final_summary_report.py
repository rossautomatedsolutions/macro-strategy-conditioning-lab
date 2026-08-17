"""Reusable table builders for Notebook 08 final research summary packet."""

from __future__ import annotations

import pandas as pd

from src.conditioning.regime_diagnostics_report import build_notebook_06_tables
from src.conditioning.transition_diagnostics_report import build_notebook_07_tables
from src.data.integration_summary import (
    build_macro_regime_category_counts,
    build_real_macro_integration_overview,
)

OPTIONAL_STRATEGY_METADATA_COLUMNS = ["strategy_name", "strategy_category", "asset_class"]


def build_strategy_coverage_summary(strategy_returns: pd.DataFrame) -> pd.DataFrame:
    """Return compact coverage metadata for the current strategy file."""
    aggregation: dict[str, tuple[str, str]] = {
        "observation_count": ("returns", "size"),
        "strategy_start": ("DATE", "min"),
        "strategy_end": ("DATE", "max"),
    }
    for column in OPTIONAL_STRATEGY_METADATA_COLUMNS:
        if column in strategy_returns.columns:
            aggregation[column] = (column, "first")

    summary = (
        strategy_returns.groupby("strategy_id")
        .agg(**aggregation)
        .reset_index()
        .sort_values("strategy_id")
        .reset_index(drop=True)
    )

    for column in OPTIONAL_STRATEGY_METADATA_COLUMNS:
        if column not in summary.columns:
            summary[column] = pd.NA

    ordered_columns = [
        "strategy_id",
        *OPTIONAL_STRATEGY_METADATA_COLUMNS,
        "observation_count",
        "strategy_start",
        "strategy_end",
    ]
    return summary.loc[:, ordered_columns]


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
    transition_window_status: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return packet caveats as a compact table."""
    strategy_start = strategy_returns["DATE"].min().date()
    strategy_end = strategy_returns["DATE"].max().date()
    realized_category_count = realized_macro_regime_counts["Macro_Regime"].nunique()
    aligned_count = len(aligned_transitions)
    transition_status = None
    if transition_window_status is not None and not transition_window_status.empty:
        transition_status = transition_window_status.iloc[0].to_dict()

    def _count_label(count: int, singular: str, plural: str | None = None) -> str:
        noun = singular if count == 1 else (plural or f"{singular}s")
        return f"{count} {noun}"

    def _incomplete_window_detail() -> str:
        parts: list[str] = []
        partial_count = int(transition_status["partial_strategy_transition_window_count"])
        missing_count = int(transition_status.get("missing_strategy_transition_window_count", 0))
        if partial_count:
            parts.append(_count_label(partial_count, "partial window"))
        if missing_count:
            parts.append(_count_label(missing_count, "zero-observation window"))
        return " and ".join(parts) if parts else "incomplete windows"

    if aligned_count == 0:
        transition_detail = (
            "Zero aligned transition rows is acceptable for the current strategy input "
            "and is not a contract failure."
        )
    elif transition_status is not None and transition_status["status"] == "incomplete_only":
        detail = "Aligned transition rows exist, but all expected per-strategy event windows are incomplete."
        if int(transition_status.get("missing_strategy_transition_window_count", 0)) > 0:
            detail += " Some expected strategy windows have zero observations anywhere in the event window."
        transition_detail = f"{detail} Aggregate transition summaries exclude incomplete windows."
    elif transition_status is not None and transition_status["status"] == "mixed":
        transition_detail = (
            f"The current strategy input includes {_count_label(aligned_count, 'aligned transition row')}. "
            f"Aggregate transition summaries use only "
            f"{_count_label(transition_status['complete_strategy_transition_window_count'], 'complete per-strategy window')} "
            f"and report {_incomplete_window_detail()} separately."
        )
    else:
        transition_detail = (
            f"The current strategy input includes {_count_label(aligned_count, 'aligned transition row')} "
            "and all expected per-strategy event windows are complete."
        )

    return pd.DataFrame(
        [
            {
                "caveat": "strategy_input_window",
                "detail": (
                    "The current strategy input is descriptive research data. "
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
                "deferred_work": "additional_strategies_if_needed",
                "detail": "Add more strategies only when needed for broader descriptive coverage; keep methodology unchanged.",
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
        "transition_window_status": notebook_07["transition_window_status"],
        "transition_window_completeness_summary": notebook_07["transition_window_completeness_summary"],
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
            transition_window_status=notebook_07["transition_window_status"],
        ),
        "deferred_work": build_deferred_work_table(),
    }
