from pathlib import Path

import pandas as pd

from src.conditioning.final_summary_report import build_notebook_08_tables
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import run_all_validations


def test_notebook_08_final_summary_packet_notebook_exists_at_canonical_path():
    assert Path("notebooks/08_final_summary_packet.ipynb").exists()


def test_notebook_08_final_summary_packet_path_uses_real_macro_files():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")

    run_all_validations(regimes, transitions, strategy_returns)
    tables = build_notebook_08_tables(regimes, transitions, strategy_returns, sparse_threshold=3, window=3)

    assert set(tables) == {
        "input_coverage_summary",
        "macro_regime_file_summary",
        "strategy_coverage_summary",
        "overlap_summary",
        "realized_macro_regime_category_counts",
        "regime_diagnostics_summary",
        "sparse_missing_regime_warnings",
        "transition_coverage_summary",
        "aligned_skipped_transition_summary",
        "aligned_transition_rows",
        "skipped_transition_rows",
        "caveats",
        "deferred_work",
    }

    input_summary = tables["input_coverage_summary"]
    assert len(input_summary) == 1
    assert input_summary.loc[0, "macro_row_count"] == 419
    assert input_summary.loc[0, "transition_row_count"] == 62
    assert input_summary.loc[0, "strategy_row_count"] == 12
    assert input_summary.loc[0, "overlap_start"] == pd.Timestamp("2023-01-31")
    assert input_summary.loc[0, "overlap_end"] == pd.Timestamp("2023-06-30")

    macro_file_summary = tables["macro_regime_file_summary"]
    assert len(macro_file_summary) == 6
    assert macro_file_summary["count"].sum() == 419

    strategy_coverage = tables["strategy_coverage_summary"]
    assert strategy_coverage.to_dict("records") == [
        {
            "strategy_id": "strat_a",
            "strategy_name": "Carry A",
            "strategy_category": "Carry",
            "asset_class": "Multi-Asset",
            "observation_count": 6,
            "strategy_start": pd.Timestamp("2023-01-31"),
            "strategy_end": pd.Timestamp("2023-06-30"),
        },
        {
            "strategy_id": "strat_b",
            "strategy_name": "Value B",
            "strategy_category": "Value",
            "asset_class": "Equity",
            "observation_count": 6,
            "strategy_start": pd.Timestamp("2023-01-31"),
            "strategy_end": pd.Timestamp("2023-06-30"),
        },
    ]

    overlap_summary = tables["overlap_summary"]
    assert overlap_summary.to_dict("records") == [
        {
            "macro_start": pd.Timestamp("1991-01-31"),
            "macro_end": pd.Timestamp("2025-12-31"),
            "strategy_start": pd.Timestamp("2023-01-31"),
            "strategy_end": pd.Timestamp("2023-06-30"),
            "overlap_start": pd.Timestamp("2023-01-31"),
            "overlap_end": pd.Timestamp("2023-06-30"),
            "transitions_inside_strategy_coverage": 0,
            "transitions_outside_strategy_coverage": 62,
        }
    ]

    realized_counts = tables["realized_macro_regime_category_counts"]
    assert realized_counts["observation_count"].sum() == 12
    assert realized_counts["strategy_count"].sum() == 2

    regime_diagnostics = tables["regime_diagnostics_summary"]
    assert len(regime_diagnostics) == 2
    assert set(regime_diagnostics["strategy_id"]) == {"strat_a", "strat_b"}

    sparse_warnings = tables["sparse_missing_regime_warnings"]
    assert not sparse_warnings.empty
    assert set(sparse_warnings["coverage_status"]).issubset({"sparse", "unobserved"})

    transition_summary = tables["transition_coverage_summary"]
    assert transition_summary.loc[0, "total_transition_rows"] == 62
    assert transition_summary.loc[0, "transitions_inside_strategy_coverage"] == 0
    assert transition_summary.loc[0, "transitions_outside_strategy_coverage"] == 62

    aligned_skipped = tables["aligned_skipped_transition_summary"]
    assert aligned_skipped.to_dict("records") == [
        {
            "aligned_transition_rows": 0,
            "skipped_transition_rows": 62,
        }
    ]

    assert tables["aligned_transition_rows"].empty
    assert len(tables["skipped_transition_rows"]) == 62

    caveats = tables["caveats"]
    assert set(caveats["caveat"]) == {
        "sample_strategy_window",
        "realized_regime_coverage",
        "transition_alignment_context",
        "research_only",
    }

    deferred_work = tables["deferred_work"]
    assert set(deferred_work["deferred_work"]) == {
        "broader_strategy_history",
        "additional_sample_strategies",
        "dashboarding_out_of_scope",
    }
