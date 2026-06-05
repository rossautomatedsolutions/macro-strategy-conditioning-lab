import pandas as pd

from src.conditioning.regime_join import join_returns_with_regimes
from src.conditioning.transition_analysis import build_transition_windows
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import audit_transition_coverage


def test_join_returns_with_regimes_shape():
    regimes = load_regimes("data/macro/regimes_example.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    joined = join_returns_with_regimes(strategy_returns, regimes)
    assert len(joined) == len(strategy_returns)
    assert "Macro_Regime" in joined.columns


def test_transition_windows_has_event_month_zero():
    regimes = load_regimes("data/macro/regimes_example.csv")
    transitions = load_transitions("data/macro/transitions_example.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    joined = join_returns_with_regimes(strategy_returns, regimes)
    events = build_transition_windows(joined, transitions, window=2)

    assert (events["relative_month"] == 0).any()
    assert {"from", "to", "transition_date"}.issubset(events.columns)


def test_transition_windows_skip_outside_strategy_coverage_cleanly():
    regimes = load_regimes("data/macro/regimes_example.csv")
    transitions = load_transitions("data/macro/transitions_example.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")
    late_start = strategy_returns.loc[strategy_returns["DATE"] >= "2023-04-30"].reset_index(drop=True)

    joined = join_returns_with_regimes(late_start, regimes)
    coverage = audit_transition_coverage(transitions, late_start)
    events = build_transition_windows(joined, transitions, window=2)

    assert coverage.outside_coverage["transition_date"].tolist() == [pd.Timestamp("2023-03-31")]
    assert pd.Timestamp("2023-03-31") not in set(events["transition_date"])
    assert set(events["transition_date"]) == set(coverage.aligned["transition_date"])
