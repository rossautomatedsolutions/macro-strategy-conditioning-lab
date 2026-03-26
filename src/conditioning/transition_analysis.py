"""Transition-centered event-window analysis (non-predictive)."""

from __future__ import annotations

import pandas as pd


def build_transition_windows(
    joined_df: pd.DataFrame,
    transitions: pd.DataFrame,
    window: int = 6,
) -> pd.DataFrame:
    """Create ±window month event panels around each macro transition date."""
    date_to_idx = {d: i for i, d in enumerate(sorted(joined_df["DATE"].unique()))}
    unique_dates = sorted(date_to_idx)

    rows = []
    for _, tr in transitions.iterrows():
        center = tr["transition_date"]
        if center not in date_to_idx:
            continue
        center_idx = date_to_idx[center]
        lo = max(0, center_idx - window)
        hi = min(len(unique_dates) - 1, center_idx + window)
        window_dates = unique_dates[lo : hi + 1]

        sub = joined_df[joined_df["DATE"].isin(window_dates)].copy()
        sub["event_month"] = sub["DATE"].map(lambda d: date_to_idx[d] - center_idx)
        sub["transition_date"] = center
        sub["from"] = tr["from"]
        sub["to"] = tr["to"]
        rows.append(sub)

    if not rows:
        return pd.DataFrame(columns=[*joined_df.columns, "event_month", "transition_date", "from", "to"])
    return pd.concat(rows, ignore_index=True)


def summarize_transition_windows(event_df: pd.DataFrame) -> pd.DataFrame:
    """Average returns by event-month around transitions by strategy."""
    if event_df.empty:
        return event_df
    return (
        event_df.groupby(["strategy_id", "event_month"])["returns"]
        .agg(mean_return="mean", median_return="median", obs="count")
        .reset_index()
    )
