from pathlib import Path

import pandas as pd

from src.conditioning.final_summary_report import build_notebook_08_tables
from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import run_all_validations

REGIME_LABEL = "Expansion / Disinflationary / Easing"


def build_regimes(dates: list[str]) -> pd.DataFrame:
    values = pd.to_datetime(dates)
    return pd.DataFrame(
        {
            "DATE": values,
            "Growth_Regime": ["Expansion"] * len(values),
            "Inflation_Regime": ["Disinflationary"] * len(values),
            "Policy_Regime": ["Easing"] * len(values),
            "Macro_Regime": [REGIME_LABEL] * len(values),
        }
    )


def build_transitions(dates: list[str]) -> pd.DataFrame:
    values = pd.to_datetime(dates)
    return pd.DataFrame(
        {
            "transition_date": values,
            "from": [REGIME_LABEL] * len(values),
            "to": [REGIME_LABEL] * len(values),
        }
    )


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
        "transition_window_status",
        "transition_window_completeness_summary",
        "aligned_skipped_transition_summary",
        "aligned_transition_rows",
        "skipped_transition_rows",
        "caveats",
        "deferred_work",
    }

    input_summary = tables["input_coverage_summary"]
    assert len(input_summary) == 1
    assert input_summary.loc[0, "macro_row_count"] == 420
    assert input_summary.loc[0, "transition_row_count"] == 62
    assert input_summary.loc[0, "strategy_row_count"] == 12
    assert input_summary.loc[0, "overlap_start"] == pd.Timestamp("2023-01-31")
    assert input_summary.loc[0, "overlap_end"] == pd.Timestamp("2023-06-30")

    macro_file_summary = tables["macro_regime_file_summary"]
    assert len(macro_file_summary) == 6
    assert macro_file_summary["count"].sum() == 420

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

    transition_window_status = tables["transition_window_status"]
    assert transition_window_status.to_dict("records") == [
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
        "strategy_input_window",
        "realized_regime_coverage",
        "transition_alignment_context",
        "research_only",
    }

    deferred_work = tables["deferred_work"]
    assert set(deferred_work["deferred_work"]) == {
        "broader_strategy_history",
        "additional_strategies_if_needed",
        "dashboarding_out_of_scope",
    }


def test_notebook_08_final_summary_packet_supports_required_only_strategy_contract():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")[
        ["DATE", "strategy_id", "returns"]
    ].copy()

    run_all_validations(regimes, transitions, strategy_returns)
    tables = build_notebook_08_tables(regimes, transitions, strategy_returns, sparse_threshold=3, window=3)

    strategy_coverage = tables["strategy_coverage_summary"]
    assert strategy_coverage["strategy_name"].isna().all()
    assert strategy_coverage["strategy_category"].isna().all()
    assert strategy_coverage["asset_class"].isna().all()
    assert strategy_coverage["observation_count"].tolist() == [6, 6]


def test_notebook_08_final_summary_packet_reports_missing_strategy_windows_separately():
    regimes = build_regimes(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])
    transitions = build_transitions(["2023-03-31"])
    strategy_returns = pd.DataFrame(
        {
            "DATE": pd.to_datetime(
                [
                    "2023-01-31",
                    "2023-02-28",
                    "2023-03-31",
                    "2023-04-30",
                    "2023-05-31",
                    "2023-01-31",
                    "2023-05-31",
                ]
            ),
            "strategy_id": ["strat_a"] * 5 + ["strat_b"] * 2,
            "returns": [0.01, -0.02, 0.03, -0.01, 0.02, 0.04, -0.03],
        }
    )

    run_all_validations(regimes, transitions, strategy_returns)
    tables = build_notebook_08_tables(regimes, transitions, strategy_returns, sparse_threshold=1, window=1)

    assert tables["transition_window_status"].to_dict("records") == [
        {
            "status": "mixed",
            "aligned_transition_count": 1,
            "aligned_transition_rows_with_any_complete_window": 1,
            "aligned_transition_rows_with_only_incomplete_windows": 0,
            "aligned_transition_rows_with_missing_windows": 1,
            "complete_strategy_transition_window_count": 1,
            "partial_strategy_transition_window_count": 0,
            "missing_strategy_transition_window_count": 1,
            "message": (
                "Aligned transition dates exist. Aggregate transition summaries use only complete per-strategy "
                "event windows; incomplete windows, including zero-observation strategy windows, "
                "are reported separately."
            ),
        }
    ]
    assert tables["transition_window_completeness_summary"].to_dict("records") == [
        {
            "strategy_transition_windows": 2,
            "complete_strategy_transition_windows": 1,
            "partial_strategy_transition_windows": 0,
            "missing_strategy_transition_windows": 1,
            "aligned_transition_rows_with_any_complete_window": 1,
            "aligned_transition_rows_with_only_incomplete_windows": 0,
            "aligned_transition_rows_with_missing_windows": 1,
            "aligned_transition_rows_all_windows_complete": 0,
        }
    ]
    assert (
        tables["caveats"].loc[tables["caveats"]["caveat"] == "transition_alignment_context", "detail"].iloc[0]
        == (
            "The current strategy input includes 1 aligned transition row. "
            "Aggregate transition summaries use only 1 complete per-strategy window "
            "and report 1 zero-observation window separately."
        )
    )
    assert (
        tables["caveats"].loc[tables["caveats"]["caveat"] == "strategy_input_window", "detail"].iloc[0]
        == "The current strategy input is descriptive research data. The current input spans 2023-01-31 through 2023-05-31."
    )
