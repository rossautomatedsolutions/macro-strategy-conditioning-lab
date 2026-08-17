import pandas as pd

from src.conditioning.regime_diagnostics_report import build_notebook_06_tables
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import run_all_validations


def test_notebook_06_real_diagnostics_path_uses_real_macro_files():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    run_all_validations(regimes, transitions, strategy_returns)
    tables = build_notebook_06_tables(regimes, transitions, strategy_returns, sparse_threshold=3)

    assert set(tables) == {
        "integration_overview",
        "transition_coverage_summary",
        "joined_preview",
        "macro_regime_observation_summary",
        "strategy_regime_diagnostics",
        "sparse_coverage",
        "sparse_warnings",
    }

    overview = tables["integration_overview"]
    assert len(overview) == 1
    assert overview.loc[0, "macro_row_count"] == 420
    assert overview.loc[0, "transition_row_count"] == 62
    assert overview.loc[0, "strategy_row_count"] == 12

    transition_summary = tables["transition_coverage_summary"]
    assert transition_summary.to_dict("records") == [
        {
            "transitions_inside_strategy_coverage": 0,
            "transitions_outside_strategy_coverage": 62,
        }
    ]

    joined_preview = tables["joined_preview"]
    assert len(joined_preview) == len(strategy_returns)
    assert set(joined_preview["strategy_id"]) == {"strat_a", "strat_b"}
    assert joined_preview["DATE"].min() == pd.Timestamp("2023-01-31")
    assert joined_preview["DATE"].max() == pd.Timestamp("2023-06-30")

    macro_summary = tables["macro_regime_observation_summary"]
    assert macro_summary["observation_count"].sum() == len(strategy_returns)
    assert {
        "Macro_Regime",
        "observation_count",
        "strategy_count",
        "average_return",
        "volatility",
        "min_return",
        "max_return",
    }.issubset(macro_summary.columns)

    regime_diagnostics = tables["strategy_regime_diagnostics"]
    assert len(regime_diagnostics) > 0
    assert {
        "strategy_id",
        "Macro_Regime",
        "obs",
        "mean_return",
        "cumulative_return",
        "volatility",
        "min_return",
        "max_return",
        "max_drawdown",
        "average_drawdown",
    }.issubset(regime_diagnostics.columns)

    sparse_coverage = tables["sparse_coverage"]
    assert not sparse_coverage.empty
    assert set(sparse_coverage["coverage_status"]).issubset({"adequate", "sparse", "unobserved"})
    assert set(sparse_coverage["sample_caveat"]) == {"Diagnostic warning only; not a trading conclusion."}

    sparse_warnings = tables["sparse_warnings"]
    assert not sparse_warnings.empty
