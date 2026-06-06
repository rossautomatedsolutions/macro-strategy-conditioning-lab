import pandas as pd

from src.conditioning.regime_join import join_returns_with_regimes
from src.data.integration_summary import (
    build_macro_regime_category_counts,
    build_real_macro_integration_overview,
)
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import run_all_validations


def test_notebook_05_real_integration_path_uses_real_macro_files():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    run_all_validations(regimes, transitions, strategy_returns)

    overview, coverage = build_real_macro_integration_overview(regimes, transitions, strategy_returns)
    joined = join_returns_with_regimes(strategy_returns, regimes)
    category_counts = build_macro_regime_category_counts(regimes)

    assert len(overview) == 1
    assert overview.loc[0, "macro_row_count"] == 419
    assert overview.loc[0, "transition_row_count"] == 62
    assert overview.loc[0, "strategy_row_count"] == 12
    assert overview.loc[0, "macro_start"] == pd.Timestamp("1991-01-31")
    assert overview.loc[0, "macro_end"] == pd.Timestamp("2025-12-31")
    assert overview.loc[0, "strategy_start"] == pd.Timestamp("2023-01-31")
    assert overview.loc[0, "strategy_end"] == pd.Timestamp("2023-06-30")
    assert overview.loc[0, "overlap_start"] == pd.Timestamp("2023-01-31")
    assert overview.loc[0, "overlap_end"] == pd.Timestamp("2023-06-30")
    assert overview.loc[0, "macro_regime_categories"] == 6
    assert overview.loc[0, "transitions_inside_strategy_coverage"] == 0
    assert overview.loc[0, "transitions_outside_strategy_coverage"] == 62

    assert coverage.aligned.empty
    assert len(coverage.outside_coverage) == 62

    assert len(joined) == len(strategy_returns)
    assert set(joined["strategy_id"]) == {"strat_a", "strat_b"}
    assert joined["DATE"].min() == pd.Timestamp("2023-01-31")
    assert joined["DATE"].max() == pd.Timestamp("2023-06-30")

    assert len(category_counts) == 6
    assert category_counts["count"].sum() == 419
