import pandas as pd

from src.conditioning.final_summary_report import build_notebook_08_tables
from src.conditioning.regime_join import join_returns_with_regimes
from src.conditioning.transition_diagnostics_report import build_notebook_07_tables
from src.data.integration_summary import build_real_macro_integration_overview
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import run_all_validations


def test_wide_strategy_sample_fixture_loads_and_validates():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_wide_sample.csv")

    run_all_validations(regimes, transitions, strategy_returns)

    assert len(strategy_returns) == 86
    assert strategy_returns["DATE"].min() == pd.Timestamp("2007-01-31")
    assert strategy_returns["DATE"].max() == pd.Timestamp("2010-07-31")
    assert set(strategy_returns["strategy_id"]) == {"strat_a", "strat_b"}


def test_wide_strategy_sample_broadens_macro_coverage_relative_to_narrow_fixture():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    narrow_strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")
    wide_strategy_returns = load_strategy_returns("data/strategies/strategy_returns_wide_sample.csv")

    narrow_overview, narrow_coverage = build_real_macro_integration_overview(
        regimes,
        transitions,
        narrow_strategy_returns,
    )
    wide_overview, wide_coverage = build_real_macro_integration_overview(
        regimes,
        transitions,
        wide_strategy_returns,
    )
    narrow_joined = join_returns_with_regimes(narrow_strategy_returns, regimes)
    wide_joined = join_returns_with_regimes(wide_strategy_returns, regimes)

    assert narrow_overview.loc[0, "overlap_start"] == pd.Timestamp("2023-01-31")
    assert narrow_overview.loc[0, "overlap_end"] == pd.Timestamp("2023-06-30")
    assert wide_overview.loc[0, "overlap_start"] == pd.Timestamp("2007-01-31")
    assert wide_overview.loc[0, "overlap_end"] == pd.Timestamp("2010-07-31")
    assert wide_overview.loc[0, "strategy_row_count"] > narrow_overview.loc[0, "strategy_row_count"]
    assert wide_joined["Macro_Regime"].nunique() > narrow_joined["Macro_Regime"].nunique()
    assert wide_joined["Macro_Regime"].nunique() == 6
    assert len(wide_coverage.aligned) > len(narrow_coverage.aligned)


def test_wide_strategy_sample_produces_aligned_transition_examples():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_wide_sample.csv")

    run_all_validations(regimes, transitions, strategy_returns)
    tables = build_notebook_07_tables(regimes, transitions, strategy_returns, window=3)

    transition_summary = tables["transition_coverage_summary"]
    assert transition_summary.loc[0, "transitions_inside_strategy_coverage"] == 13
    assert transition_summary.loc[0, "transitions_outside_strategy_coverage"] == 49

    aligned = tables["aligned_transitions"]
    assert len(aligned) == 13
    assert aligned["transition_date"].min() == pd.Timestamp("2007-01-31")
    assert aligned["transition_date"].max() == pd.Timestamp("2010-07-31")

    status = tables["transition_window_status"]
    assert status.to_dict("records") == [
        {
            "status": "mixed",
            "aligned_transition_count": 13,
            "aligned_transition_rows_with_any_complete_window": 9,
            "aligned_transition_rows_with_only_incomplete_windows": 4,
            "aligned_transition_rows_with_missing_windows": 0,
            "complete_strategy_transition_window_count": 18,
            "partial_strategy_transition_window_count": 8,
            "missing_strategy_transition_window_count": 0,
            "message": (
                "Aligned transition dates exist. Aggregate transition summaries use only complete per-strategy "
                "event windows; partial windows are reported separately."
            ),
        }
    ]

    completeness = tables["transition_window_completeness_summary"]
    assert completeness.to_dict("records") == [
        {
            "strategy_transition_windows": 26,
            "complete_strategy_transition_windows": 18,
            "partial_strategy_transition_windows": 8,
            "missing_strategy_transition_windows": 0,
            "aligned_transition_rows_with_any_complete_window": 9,
            "aligned_transition_rows_with_only_incomplete_windows": 4,
            "aligned_transition_rows_with_missing_windows": 0,
            "aligned_transition_rows_all_windows_complete": 9,
        }
    ]

    diagnostics = tables["transition_window_diagnostics"]
    assert set(diagnostics["window_status"]) == {"complete", "partial"}
    assert len(diagnostics) == 26

    assert not tables["transition_windows"].empty
    assert not tables["transition_window_summary"].empty
    assert not tables["transition_cumulative_profile"].empty


def test_final_summary_packet_builds_with_wide_strategy_sample():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_wide_sample.csv")

    run_all_validations(regimes, transitions, strategy_returns)
    tables = build_notebook_08_tables(regimes, transitions, strategy_returns, sparse_threshold=3, window=3)

    strategy_coverage = tables["strategy_coverage_summary"]
    assert strategy_coverage["observation_count"].tolist() == [43, 43]

    realized_counts = tables["realized_macro_regime_category_counts"]
    assert realized_counts["Macro_Regime"].nunique() == 6
    assert realized_counts["observation_count"].sum() == 86

    aligned_skipped = tables["aligned_skipped_transition_summary"]
    assert aligned_skipped.to_dict("records") == [
        {
            "aligned_transition_rows": 13,
            "skipped_transition_rows": 49,
        }
    ]

    transition_window_status = tables["transition_window_status"]
    assert transition_window_status.loc[0, "status"] == "mixed"

    transition_window_completeness_summary = tables["transition_window_completeness_summary"]
    assert transition_window_completeness_summary.loc[0, "complete_strategy_transition_windows"] == 18
    assert transition_window_completeness_summary.loc[0, "partial_strategy_transition_windows"] == 8
    assert transition_window_completeness_summary.loc[0, "missing_strategy_transition_windows"] == 0

    caveats = tables["caveats"]
    assert set(caveats["caveat"]) == {
        "strategy_input_window",
        "realized_regime_coverage",
        "transition_alignment_context",
        "research_only",
    }
    assert (
        caveats.loc[caveats["caveat"] == "transition_alignment_context", "detail"].iloc[0]
        == (
            "The current strategy input includes 13 aligned transition rows. "
            "Aggregate transition summaries use only 18 complete per-strategy windows "
            "and report 8 partial windows separately."
        )
    )
