"""Reusable table builders for Notebook 07 transition-event diagnostics."""

from __future__ import annotations

import pandas as pd

from src.conditioning.regime_join import join_returns_with_regimes
from src.conditioning.transition_analysis import (
    WINDOW_DIAGNOSTIC_COLUMNS,
    WINDOW_GROUP_COLUMNS,
    build_transition_windows,
    cumulative_transition_profile,
    summarize_transition_windows,
)
from src.data.integration_summary import build_real_macro_integration_overview


def build_expected_transition_window_diagnostics(
    transition_windows: pd.DataFrame,
    aligned_transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
    *,
    window: int,
) -> pd.DataFrame:
    """Return one diagnostic row for every expected strategy/transition event window."""
    columns = [*WINDOW_GROUP_COLUMNS, *WINDOW_DIAGNOSTIC_COLUMNS]
    if aligned_transitions.empty or strategy_returns.empty:
        return pd.DataFrame(columns=columns)

    strategy_ids = (
        pd.DataFrame({"strategy_id": sorted(strategy_returns["strategy_id"].unique())})
        .sort_values("strategy_id")
        .reset_index(drop=True)
    )
    aligned_keys = (
        aligned_transitions[["transition_date", "from", "to"]]
        .drop_duplicates()
        .sort_values(["transition_date", "from", "to"])
        .reset_index(drop=True)
    )
    expected = (
        strategy_ids.assign(_key=1)
        .merge(aligned_keys.assign(_key=1), on="_key", how="inner")
        .drop(columns="_key")
    )

    observed = (
        transition_windows.loc[:, columns].drop_duplicates().reset_index(drop=True)
        if not transition_windows.empty
        else pd.DataFrame(columns=columns)
    )
    diagnostics = expected.merge(observed, on=WINDOW_GROUP_COLUMNS, how="left", validate="one_to_one")
    expected_relative_months = tuple(range(-window, window + 1))
    missing_mask = diagnostics["window_status"].isna()

    diagnostics["expected_relative_month_count"] = diagnostics["expected_relative_month_count"].fillna(
        len(expected_relative_months)
    )
    diagnostics["observed_relative_month_count"] = diagnostics["observed_relative_month_count"].fillna(0)
    diagnostics["is_complete_window"] = diagnostics["is_complete_window"].fillna(False)
    diagnostics["has_event_month"] = diagnostics["has_event_month"].fillna(False)

    if missing_mask.any():
        missing_index = diagnostics.index[missing_mask]
        diagnostics.loc[missing_mask, "window_status"] = "missing"
        diagnostics.loc[missing_mask, "observed_relative_months"] = pd.Series(
            [tuple()] * len(missing_index),
            index=missing_index,
            dtype=object,
        )
        diagnostics.loc[missing_mask, "missing_relative_months"] = pd.Series(
            [expected_relative_months] * len(missing_index),
            index=missing_index,
            dtype=object,
        )

    diagnostics["observed_relative_month_count"] = diagnostics["observed_relative_month_count"].astype(int)
    diagnostics["expected_relative_month_count"] = diagnostics["expected_relative_month_count"].astype(int)

    return diagnostics.sort_values(["transition_date", "strategy_id"]).reset_index(drop=True)


def build_transition_window_completeness_summary(
    transition_window_diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """Return one-row completeness counts for expected per-strategy event windows."""
    if transition_window_diagnostics.empty:
        return pd.DataFrame(
            [
                {
                    "strategy_transition_windows": 0,
                    "complete_strategy_transition_windows": 0,
                    "partial_strategy_transition_windows": 0,
                    "missing_strategy_transition_windows": 0,
                    "aligned_transition_rows_with_any_complete_window": 0,
                    "aligned_transition_rows_with_only_incomplete_windows": 0,
                    "aligned_transition_rows_with_missing_windows": 0,
                    "aligned_transition_rows_all_windows_complete": 0,
                }
            ]
        )

    diagnostics = transition_window_diagnostics[
        [
            "strategy_id",
            "transition_date",
            "from",
            "to",
            "window_status",
            "is_complete_window",
        ]
    ].drop_duplicates()
    complete_dates = set(diagnostics.loc[diagnostics["is_complete_window"], "transition_date"])
    all_dates = set(diagnostics["transition_date"])
    incomplete_only_dates = all_dates - complete_dates
    missing_dates = set(
        diagnostics.loc[diagnostics["window_status"] == "missing", "transition_date"]
    )
    all_complete_dates = set(
        diagnostics.groupby("transition_date")["is_complete_window"].all().loc[lambda s: s].index.tolist()
    )

    return pd.DataFrame(
        [
            {
                "strategy_transition_windows": len(diagnostics),
                "complete_strategy_transition_windows": int(diagnostics["is_complete_window"].sum()),
                "partial_strategy_transition_windows": int((diagnostics["window_status"] == "partial").sum()),
                "missing_strategy_transition_windows": int((diagnostics["window_status"] == "missing").sum()),
                "aligned_transition_rows_with_any_complete_window": len(complete_dates),
                "aligned_transition_rows_with_only_incomplete_windows": len(incomplete_only_dates),
                "aligned_transition_rows_with_missing_windows": len(missing_dates),
                "aligned_transition_rows_all_windows_complete": len(all_complete_dates),
            }
        ]
    )


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


def build_transition_window_status(
    aligned_transitions: pd.DataFrame,
    transition_window_completeness_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Return a compact status table for aligned transition event windows."""
    if aligned_transitions.empty:
        return pd.DataFrame(
            [
                {
                    "status": "empty",
                    "aligned_transition_count": 0,
                    "aligned_transition_rows_with_any_complete_window": 0,
                    "aligned_transition_rows_with_only_incomplete_windows": 0,
                    "aligned_transition_rows_with_missing_windows": 0,
                    "complete_strategy_transition_window_count": 0,
                    "partial_strategy_transition_window_count": 0,
                    "missing_strategy_transition_window_count": 0,
                    "message": (
                        "No transition dates overlap the current strategy window; "
                        "this is acceptable when the supplied strategy history does not cover transition months "
                        "and is not a contract failure."
                    ),
                }
            ]
        )

    completeness = transition_window_completeness_summary.iloc[0]
    complete_windows = int(completeness["complete_strategy_transition_windows"])
    partial_windows = int(completeness["partial_strategy_transition_windows"])
    missing_windows = int(completeness["missing_strategy_transition_windows"])
    complete_transition_rows = int(completeness["aligned_transition_rows_with_any_complete_window"])
    incomplete_only_transition_rows = int(completeness["aligned_transition_rows_with_only_incomplete_windows"])
    missing_transition_rows = int(completeness["aligned_transition_rows_with_missing_windows"])

    if complete_windows == 0:
        status = "incomplete_only"
        if missing_windows > 0:
            message = (
                "Aligned transition dates exist, but all expected per-strategy event windows are incomplete. "
                "Some strategies have no observations anywhere in the event window. "
                "Aggregate transition summaries exclude incomplete windows."
            )
        else:
            message = (
                "Aligned transition dates exist, but all expected per-strategy event windows are incomplete. "
                "Aggregate transition summaries exclude incomplete windows."
            )
    elif partial_windows > 0 or missing_windows > 0:
        status = "mixed"
        if missing_windows > 0:
            message = (
                "Aligned transition dates exist. Aggregate transition summaries use only complete per-strategy "
                "event windows; incomplete windows, including zero-observation strategy windows, "
                "are reported separately."
            )
        else:
            message = (
                "Aligned transition dates exist. Aggregate transition summaries use only complete per-strategy "
                "event windows; partial windows are reported separately."
            )
    else:
        status = "complete"
        message = "Aligned transition dates exist and all expected per-strategy event windows are complete."

    return pd.DataFrame(
        [
            {
                "status": status,
                "aligned_transition_count": len(aligned_transitions),
                "aligned_transition_rows_with_any_complete_window": complete_transition_rows,
                "aligned_transition_rows_with_only_incomplete_windows": incomplete_only_transition_rows,
                "aligned_transition_rows_with_missing_windows": missing_transition_rows,
                "complete_strategy_transition_window_count": complete_windows,
                "partial_strategy_transition_window_count": partial_windows,
                "missing_strategy_transition_window_count": missing_windows,
                "message": message,
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
    transition_window_diagnostics = build_expected_transition_window_diagnostics(
        transition_windows,
        coverage.aligned,
        strategy_returns,
        window=window,
    )
    transition_window_completeness_summary = build_transition_window_completeness_summary(
        transition_window_diagnostics
    )

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
        "transition_window_status": build_transition_window_status(
            coverage.aligned,
            transition_window_completeness_summary,
        ),
        "transition_window_completeness_summary": transition_window_completeness_summary,
        "transition_window_diagnostics": transition_window_diagnostics,
        "transition_windows": transition_windows,
        "transition_window_summary": summarize_transition_windows(transition_windows, complete_only=True),
        "transition_cumulative_profile": cumulative_transition_profile(transition_windows, complete_only=True),
    }
