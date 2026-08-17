import pandas as pd

from src.conditioning.transition_diagnostics_report import build_notebook_07_tables
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import run_all_validations


def test_notebook_07_transition_diagnostics_path_uses_real_macro_files():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    run_all_validations(regimes, transitions, strategy_returns)
    tables = build_notebook_07_tables(regimes, transitions, strategy_returns, window=3)

    assert set(tables) == {
        "integration_overview",
        "transition_coverage_summary",
        "aligned_transitions",
        "outside_coverage_transitions",
        "transition_window_status",
        "transition_window_completeness_summary",
        "transition_window_diagnostics",
        "transition_windows",
        "transition_window_summary",
        "transition_cumulative_profile",
    }

    overview = tables["integration_overview"]
    assert len(overview) == 1
    assert overview.loc[0, "macro_row_count"] == 420
    assert overview.loc[0, "transition_row_count"] == 62
    assert overview.loc[0, "strategy_row_count"] == 12
    assert overview.loc[0, "transitions_inside_strategy_coverage"] == 0
    assert overview.loc[0, "transitions_outside_strategy_coverage"] == 62

    transition_summary = tables["transition_coverage_summary"]
    assert transition_summary.to_dict("records") == [
        {
            "total_transition_rows": 62,
            "transitions_inside_strategy_coverage": 0,
            "transitions_outside_strategy_coverage": 62,
            "earliest_transition_date": pd.Timestamp("1993-12-31"),
            "latest_transition_date": pd.Timestamp("2025-06-30"),
            "strategy_start": pd.Timestamp("2023-01-31"),
            "strategy_end": pd.Timestamp("2023-06-30"),
        }
    ]

    aligned = tables["aligned_transitions"]
    assert aligned.empty

    outside_coverage = tables["outside_coverage_transitions"]
    assert len(outside_coverage) == 62
    assert list(outside_coverage.columns) == ["transition_date", "from", "to"]

    window_status = tables["transition_window_status"]
    assert window_status.to_dict("records") == [
        {
            "status": "empty",
            "aligned_transition_count": 0,
            "aligned_transition_rows_with_any_complete_window": 0,
            "aligned_transition_rows_with_only_incomplete_windows": 0,
            "aligned_transition_rows_with_missing_windows": 0,
            "complete_strategy_transition_window_count": 0,
            "partial_strategy_transition_window_count": 0,
            "missing_strategy_transition_window_count": 0,
            "message": (
                "No transition dates overlap the current strategy window; "
                "this is acceptable when the supplied strategy history does not cover transition months "
                "and is not a contract failure."
            ),
        }
    ]

    completeness = tables["transition_window_completeness_summary"]
    assert completeness.to_dict("records") == [
        {
            "strategy_transition_windows": 0,
            "complete_strategy_transition_windows": 0,
            "partial_strategy_transition_windows": 0,
            "missing_strategy_transition_windows": 0,
            "aligned_transition_rows_with_any_complete_window": 0,
            "aligned_transition_rows_with_only_incomplete_windows": 0,
            "aligned_transition_rows_with_missing_windows": 0,
            "aligned_transition_rows_all_windows_complete": 0,
        }
    ]

    diagnostics = tables["transition_window_diagnostics"]
    assert diagnostics.empty

    assert tables["transition_windows"].empty
    assert tables["transition_window_summary"].empty
    assert tables["transition_cumulative_profile"].empty
