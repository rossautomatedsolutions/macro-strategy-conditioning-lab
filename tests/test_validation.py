import pandas as pd
import pytest

from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import run_all_validations, validate_strategy_returns


def test_run_all_validations_passes_on_examples():
    regimes = load_regimes("data/macro/regimes_example.csv")
    transitions = load_transitions("data/macro/transitions_example.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    run_all_validations(regimes, transitions, strategy_returns)


def test_strategy_date_misalignment_raises():
    regimes = load_regimes("data/macro/regimes_example.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    bad = strategy_returns.copy()
    bad.loc[0, "DATE"] = pd.Timestamp("2022-12-31")

    with pytest.raises(ValueError, match="dates not in macro regimes"):
        validate_strategy_returns(bad, regimes)
