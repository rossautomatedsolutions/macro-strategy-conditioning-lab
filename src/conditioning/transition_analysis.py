"""Transition-centered event-window analysis (non-predictive)."""

from __future__ import annotations

import pandas as pd

from src.conditioning.regime_stats import compute_cumulative_returns


def build_transition_windows(
    joined_df: pd.DataFrame,
    transitions: pd.DataFrame,
    window: int = 3,
) -> pd.DataFrame:
    """Create descriptive event windows around each historical transition date."""
    ordered = joined_df.sort_values(["strategy_id", "DATE"]).copy()
    available_dates = sorted(ordered["DATE"].unique())
    date_to_idx = {date: idx for idx, date in enumerate(available_dates)}

    rows: list[pd.DataFrame] = []
    for _, transition in transitions.iterrows():
        transition_date = transition["transition_date"]
        if transition_date not in date_to_idx:
            continue

        center_idx = date_to_idx[transition_date]
        lo = max(0, center_idx - window)
        hi = min(len(available_dates) - 1, center_idx + window)
        window_dates = available_dates[lo : hi + 1]

        event_window = ordered[ordered["DATE"].isin(window_dates)].copy()
        event_window["relative_month"] = event_window["DATE"].map(lambda d: date_to_idx[d] - center_idx)
        event_window["transition_date"] = transition_date
        event_window["from"] = transition["from"]
        event_window["to"] = transition["to"]
        rows.append(event_window)

    columns = [*ordered.columns, "relative_month", "transition_date", "from", "to"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.concat(rows, ignore_index=True)


def summarize_transition_windows(event_df: pd.DataFrame) -> pd.DataFrame:
    """Average returns and volatility by relative month around transitions."""
    if event_df.empty:
        return pd.DataFrame(
            columns=["strategy_id", "relative_month", "mean_return", "median_return", "volatility", "obs"]
        )

    return (
        event_df.groupby(["strategy_id", "relative_month"])["returns"]
        .agg(mean_return="mean", median_return="median", volatility="std", obs="count")
        .reset_index()
    )


def cumulative_transition_profile(event_df: pd.DataFrame) -> pd.DataFrame:
    """Compute average cumulative behavior around transitions by strategy."""
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
