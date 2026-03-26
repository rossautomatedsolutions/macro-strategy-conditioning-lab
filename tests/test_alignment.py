from src.conditioning.regime_join import join_returns_with_regimes
from src.conditioning.transition_analysis import build_transition_windows
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions


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

    assert (events["event_month"] == 0).any()
    assert {"from", "to", "transition_date"}.issubset(events.columns)
