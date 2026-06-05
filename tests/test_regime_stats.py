import pandas as pd

from src.conditioning.regime_stats import (
    compute_cumulative_returns,
    compute_drawdown_series,
    drawdown_by_regime,
    risk_summary_by_regime,
    volatility_by_regime,
)


def build_sample_joined() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "DATE": pd.to_datetime(
                [
                    "2023-01-31",
                    "2023-02-28",
                    "2023-03-31",
                    "2023-01-31",
                    "2023-02-28",
                    "2023-03-31",
                ]
            ),
            "strategy_id": ["strat_a", "strat_a", "strat_a", "strat_b", "strat_b", "strat_b"],
            "returns": [0.10, -0.20, 0.05, 0.02, -0.01, -0.03],
            "Macro_Regime": [
                "Expansion / Disinflationary / Easing",
                "Expansion / Disinflationary / Easing",
                "Contraction / Inflationary / Tightening",
                "Expansion / Disinflationary / Easing",
                "Expansion / Disinflationary / Easing",
                "Contraction / Inflationary / Tightening",
            ],
        }
    )


def test_compute_cumulative_returns_is_correct():
    returns = pd.Series([0.10, -0.20, 0.05])
    cumulative = compute_cumulative_returns(returns)

    expected = pd.Series([1.10, 0.88, 0.924])
    pd.testing.assert_series_equal(cumulative.reset_index(drop=True), expected, check_names=False)


def test_compute_drawdown_series_is_correct():
    returns = pd.Series([0.10, -0.20, 0.05])
    drawdown = compute_drawdown_series(returns)

    expected = pd.Series([0.0, -0.20, -0.16])
    pd.testing.assert_series_equal(drawdown.reset_index(drop=True).round(8), expected.round(8), check_names=False)


def test_drawdown_by_regime_reports_max_and_average_drawdown():
    joined = build_sample_joined()
    summary = drawdown_by_regime(joined)

    strat_a_expansion = summary[
        (summary["strategy_id"] == "strat_a") & (summary["Macro_Regime"] == "Expansion / Disinflationary / Easing")
    ].iloc[0]
    assert round(strat_a_expansion["max_drawdown"], 8) == -0.20
    assert round(strat_a_expansion["average_drawdown"], 8) == -0.10


def test_risk_summary_by_regime_handles_one_strategy():
    joined = build_sample_joined()
    one_strategy = joined[joined["strategy_id"] == "strat_a"].copy()

    summary = risk_summary_by_regime(one_strategy)

    assert set(summary["strategy_id"]) == {"strat_a"}
    assert {"volatility", "worst_monthly_return", "tail_return_5pct", "max_drawdown", "average_drawdown"}.issubset(
        summary.columns
    )


def test_risk_summary_by_regime_handles_multiple_strategies():
    joined = build_sample_joined()
    summary = risk_summary_by_regime(joined)

    assert set(summary["strategy_id"]) == {"strat_a", "strat_b"}
    assert len(summary) == 4


def test_regime_stats_do_not_mutate_input_dataframes():
    joined = build_sample_joined()
    original = joined.copy(deep=True)

    drawdown_by_regime(joined)
    risk_summary_by_regime(joined)
    volatility_by_regime(joined)

    pd.testing.assert_frame_equal(joined, original)
