import pandas as pd

from src.conditioning.regime_join import join_returns_with_regimes
from src.conditioning.regime_stats import regime_diagnostics_by_regime
from src.data.integration_summary import build_real_macro_integration_overview, build_sparse_regime_coverage_table
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import run_all_validations


def test_notebook_06_real_regime_diagnostics_path_uses_real_macro_files():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    run_all_validations(regimes, transitions, strategy_returns)

    overview, coverage = build_real_macro_integration_overview(regimes, transitions, strategy_returns)
    joined = join_returns_with_regimes(strategy_returns, regimes)
    diagnostics = regime_diagnostics_by_regime(joined)
    coverage_table = build_sparse_regime_coverage_table(joined, regimes, sparse_threshold=3)

    assert len(overview) == 1
    assert overview.loc[0, "macro_row_count"] == 419
    assert overview.loc[0, "transitions_inside_strategy_coverage"] == 0
    assert overview.loc[0, "transitions_outside_strategy_coverage"] == 62
    assert coverage.aligned.empty
    assert len(coverage.outside_coverage) == 62

    assert len(joined) == 12
    assert joined["Macro_Regime"].nunique() == 1

    assert len(diagnostics) == 2
    assert set(diagnostics["strategy_id"]) == {"strat_a", "strat_b"}
    assert set(diagnostics["Macro_Regime"]) == {"Expansion / Inflationary / Tightening"}
    assert diagnostics["obs"].tolist() == [6, 6]

    strat_a = diagnostics[diagnostics["strategy_id"] == "strat_a"].iloc[0]
    assert strat_a["mean_return"] == pd.Series([0.012, -0.008, 0.006, -0.015, 0.011, 0.004]).mean()
    assert round(strat_a["cumulative_return"], 8) == 0.00974396
    assert strat_a["min_return"] == -0.015
    assert strat_a["max_return"] == 0.012

    assert len(coverage_table) == 12
    assert set(coverage_table["coverage_status"]) == {"adequate", "unobserved"}
    assert (coverage_table["coverage_status"] == "unobserved").sum() == 10
    assert (
        coverage_table.loc[coverage_table["Macro_Regime"] == "Expansion / Inflationary / Tightening", "coverage_status"]
        == "adequate"
    ).all()
