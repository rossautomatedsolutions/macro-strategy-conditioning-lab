"""Transition-centered event-window analysis (non-predictive)."""

from __future__ import annotations

import pandas as pd

from src.conditioning.regime_stats import compute_cumulative_returns

WINDOW_GROUP_COLUMNS = ["strategy_id", "transition_date", "from", "to"]
WINDOW_DIAGNOSTIC_COLUMNS = [
    "window_status",
    "is_complete_window",
    "has_event_month",
    "observed_relative_month_count",
    "expected_relative_month_count",
    "observed_relative_months",
    "missing_relative_months",
]


def _calendar_month_offsets(dates: pd.Series, transition_date: pd.Timestamp) -> pd.Series:
    """Return whole-calendar-month offsets from *transition_date*."""
    return ((dates.dt.year - transition_date.year) * 12 + (dates.dt.month - transition_date.month)).astype(int)


def build_transition_window_diagnostics(event_df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Summarize completeness for each strategy/transition event window."""
    columns = [*WINDOW_GROUP_COLUMNS, *WINDOW_DIAGNOSTIC_COLUMNS]
    if event_df.empty:
        return pd.DataFrame(columns=columns)

    expected_relative_months = tuple(range(-window, window + 1))
    expected_set = set(expected_relative_months)
    rows: list[dict] = []

    for group_keys, grp in event_df.groupby(WINDOW_GROUP_COLUMNS, sort=True):
        observed_relative_months = tuple(sorted(grp["relative_month"].astype(int).unique()))
        observed_set = set(observed_relative_months)
        missing_relative_months = tuple(month for month in expected_relative_months if month not in observed_set)
        is_complete_window = observed_set == expected_set
        rows.append(
            {
                "strategy_id": group_keys[0],
                "transition_date": group_keys[1],
                "from": group_keys[2],
                "to": group_keys[3],
                "window_status": "complete" if is_complete_window else "partial",
                "is_complete_window": is_complete_window,
                "has_event_month": 0 in observed_set,
                "observed_relative_month_count": len(observed_relative_months),
                "expected_relative_month_count": len(expected_relative_months),
                "observed_relative_months": observed_relative_months,
                "missing_relative_months": missing_relative_months,
            }
        )

    return pd.DataFrame(rows).sort_values(["transition_date", "strategy_id"]).reset_index(drop=True)


def build_transition_windows(
    joined_df: pd.DataFrame,
    transitions: pd.DataFrame,
    window: int = 3,
) -> pd.DataFrame:
    """Create descriptive event windows around each historical transition date."""
    ordered = joined_df.sort_values(["strategy_id", "DATE"]).copy()
    available_dates = set(ordered["DATE"])

    rows: list[pd.DataFrame] = []
    for _, transition in transitions.iterrows():
        transition_date = transition["transition_date"]
        if transition_date not in available_dates:
            continue

        relative_month = _calendar_month_offsets(ordered["DATE"], transition_date)
        event_window = ordered.loc[relative_month.between(-window, window)].copy()
        if event_window.empty:
            continue

        event_window["relative_month"] = _calendar_month_offsets(event_window["DATE"], transition_date)
        event_window["transition_date"] = transition_date
        event_window["from"] = transition["from"]
        event_window["to"] = transition["to"]
        rows.append(event_window)

    columns = [*ordered.columns, "relative_month", "transition_date", "from", "to", *WINDOW_DIAGNOSTIC_COLUMNS]
    if not rows:
        return pd.DataFrame(columns=columns)

    event_df = pd.concat(rows, ignore_index=True)
    diagnostics = build_transition_window_diagnostics(event_df, window=window)
    return (
        event_df.merge(diagnostics, on=WINDOW_GROUP_COLUMNS, how="left", validate="many_to_one")
        .sort_values(["transition_date", "strategy_id", "DATE"])
        .reset_index(drop=True)
    )


def summarize_transition_windows(event_df: pd.DataFrame, *, complete_only: bool = False) -> pd.DataFrame:
    """Average returns and volatility by relative month around transitions."""
    if complete_only and "is_complete_window" in event_df.columns:
        event_df = event_df.loc[event_df["is_complete_window"]].copy()

    if event_df.empty:
        return pd.DataFrame(
            columns=["strategy_id", "relative_month", "mean_return", "median_return", "volatility", "obs"]
        )

    return (
        event_df.groupby(["strategy_id", "relative_month"])["returns"]
        .agg(mean_return="mean", median_return="median", volatility="std", obs="count")
        .reset_index()
    )


def cumulative_transition_profile(event_df: pd.DataFrame, *, complete_only: bool = False) -> pd.DataFrame:
    """Compute average cumulative behavior around transitions by strategy."""
    if complete_only and "is_complete_window" in event_df.columns:
        event_df = event_df.loc[event_df["is_complete_window"]].copy()

    if event_df.empty:
        return pd.DataFrame(columns=["strategy_id", "relative_month", "mean_cumulative_return", "obs"])

    rows: list[dict] = []
    grouped = event_df.groupby(["strategy_id", "transition_date"], sort=True)
    for (strategy_id, transition_date), grp in grouped:
        ordered = grp.sort_values("relative_month")
        cumulative = compute_cumulative_returns(ordered["returns"])
        for relative_month, value in zip(ordered["relative_month"], cumulative, strict=False):
            rows.append(
                {
                    "strategy_id": strategy_id,
                    "transition_date": transition_date,
                    "relative_month": relative_month,
                    "cumulative_return": float(value),
                }
            )

    cumulative_df = pd.DataFrame(rows)
    return (
        cumulative_df.groupby(["strategy_id", "relative_month"])["cumulative_return"]
        .agg(mean_cumulative_return="mean", obs="count")
        .reset_index()
    )
