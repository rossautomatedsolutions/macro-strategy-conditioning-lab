"""Plotly chart constructors for regime-conditional diagnostics."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .regime_colors import DEFAULT_REGIME_COLOR, REGIME_COLORS


def plot_regime_box(joined_df: pd.DataFrame, strategy_id: str) -> go.Figure:
    """Return distribution of returns grouped by macro regime."""
    sub = joined_df[joined_df["strategy_id"] == strategy_id]
    fig = px.box(
        sub,
        x="Macro_Regime",
        y="returns",
        color="Macro_Regime",
        color_discrete_map={k: REGIME_COLORS.get(k, DEFAULT_REGIME_COLOR) for k in sub["Macro_Regime"].unique()},
        title=f"Return Distribution by Regime — {strategy_id}",
    )
    fig.update_layout(xaxis_title="Macro Regime", yaxis_title="Monthly Return")
    return fig


def plot_drawdown_path(joined_df: pd.DataFrame, strategy_id: str) -> go.Figure:
    """Plot cumulative drawdown path for a strategy over time."""
    sub = joined_df[joined_df["strategy_id"] == strategy_id].sort_values("DATE")
    cum = (1 + sub["returns"]).cumprod()
    dd = (cum / cum.cummax()) - 1

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub["DATE"], y=dd, mode="lines", name="Drawdown"))
    fig.update_layout(title=f"Drawdown Path — {strategy_id}", xaxis_title="Date", yaxis_title="Drawdown")
    return fig


def plot_transition_profile(summary_df: pd.DataFrame, strategy_id: str) -> go.Figure:
    """Plot average returns by event month around transitions."""
    sub = summary_df[summary_df["strategy_id"] == strategy_id]
    fig = px.line(sub, x="event_month", y="mean_return", markers=True, title=f"Transition Profile — {strategy_id}")
    fig.add_vline(x=0, line_dash="dash", line_color="black")
    fig.update_layout(xaxis_title="Months from Transition", yaxis_title="Average Return")
    return fig
