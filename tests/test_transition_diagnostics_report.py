import pandas as pd

from src.conditioning.transition_diagnostics_report import build_notebook_07_tables


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


def build_strategy_returns(dates: list[str]) -> pd.DataFrame:
    values = pd.to_datetime(dates)
    return pd.DataFrame(
        {
            "DATE": values,
            "strategy_id": ["strat_a"] * len(values),
            "returns": [0.01, -0.02, 0.03, -0.01, 0.02][: len(values)],
        }
    )


def test_transition_window_status_reports_complete_windows():
    regimes = build_regimes(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])
    transitions = build_transitions(["2023-03-31"])
    strategy_returns = build_strategy_returns(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])

    tables = build_notebook_07_tables(regimes, transitions, strategy_returns, window=2)

    assert tables["transition_window_status"].to_dict("records") == [
        {
            "status": "complete",
            "aligned_transition_count": 1,
            "aligned_transition_rows_with_any_complete_window": 1,
            "aligned_transition_rows_with_only_incomplete_windows": 0,
            "aligned_transition_rows_with_missing_windows": 0,
            "complete_strategy_transition_window_count": 1,
            "partial_strategy_transition_window_count": 0,
            "missing_strategy_transition_window_count": 0,
            "message": "Aligned transition dates exist and all expected per-strategy event windows are complete.",
        }
    ]


def test_transition_window_status_reports_left_edge_truncation():
    regimes = build_regimes(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])
    transitions = build_transitions(["2023-01-31"])
    strategy_returns = build_strategy_returns(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])

    tables = build_notebook_07_tables(regimes, transitions, strategy_returns, window=2)

    assert tables["transition_window_status"].loc[0, "status"] == "incomplete_only"
    assert tables["transition_window_completeness_summary"].loc[0, "partial_strategy_transition_windows"] == 1
    assert tables["transition_window_completeness_summary"].loc[0, "missing_strategy_transition_windows"] == 0
    assert tables["transition_window_summary"].empty


def test_transition_window_status_reports_right_edge_truncation():
    regimes = build_regimes(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])
    transitions = build_transitions(["2023-05-31"])
    strategy_returns = build_strategy_returns(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])

    tables = build_notebook_07_tables(regimes, transitions, strategy_returns, window=2)

    assert tables["transition_window_status"].loc[0, "status"] == "incomplete_only"
    assert tables["transition_window_completeness_summary"].loc[0, "partial_strategy_transition_windows"] == 1
    assert tables["transition_window_completeness_summary"].loc[0, "missing_strategy_transition_windows"] == 0
    assert tables["transition_window_summary"].empty


def test_transition_window_status_reports_both_side_truncation():
    regimes = build_regimes(["2023-02-28", "2023-03-31", "2023-04-30"])
    transitions = build_transitions(["2023-03-31"])
    strategy_returns = build_strategy_returns(["2023-02-28", "2023-03-31", "2023-04-30"])

    tables = build_notebook_07_tables(regimes, transitions, strategy_returns, window=2)

    assert tables["transition_window_status"].loc[0, "status"] == "incomplete_only"
    assert tables["transition_window_completeness_summary"].loc[0, "complete_strategy_transition_windows"] == 0
    assert tables["transition_window_completeness_summary"].loc[0, "partial_strategy_transition_windows"] == 1
    assert tables["transition_window_completeness_summary"].loc[0, "missing_strategy_transition_windows"] == 0
    assert tables["transition_window_summary"].empty


def test_transition_window_status_reports_mixed_complete_and_partial_windows():
    regimes = build_regimes(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])
    transitions = build_transitions(["2023-01-31", "2023-03-31"])
    strategy_returns = build_strategy_returns(["2023-01-31", "2023-02-28", "2023-03-31", "2023-04-30", "2023-05-31"])

    tables = build_notebook_07_tables(regimes, transitions, strategy_returns, window=2)

    assert tables["transition_window_status"].to_dict("records") == [
        {
            "status": "mixed",
            "aligned_transition_count": 2,
            "aligned_transition_rows_with_any_complete_window": 1,
            "aligned_transition_rows_with_only_incomplete_windows": 1,
            "aligned_transition_rows_with_missing_windows": 0,
            "complete_strategy_transition_window_count": 1,
            "partial_strategy_transition_window_count": 1,
            "missing_strategy_transition_window_count": 0,
            "message": (
                "Aligned transition dates exist. Aggregate transition summaries use only complete per-strategy "
                "event windows; partial windows are reported separately."
            ),
        }
    ]
    assert set(tables["transition_window_diagnostics"]["window_status"]) == {"complete", "partial"}
    assert not tables["transition_window_summary"].empty
    assert not tables["transition_cumulative_profile"].empty


def test_transition_window_diagnostics_include_missing_strategy_windows():
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

    tables = build_notebook_07_tables(regimes, transitions, strategy_returns, window=1)

    assert tables["transition_window_diagnostics"].to_dict("records") == [
        {
            "strategy_id": "strat_a",
            "transition_date": pd.Timestamp("2023-03-31"),
            "from": REGIME_LABEL,
            "to": REGIME_LABEL,
            "window_status": "complete",
            "is_complete_window": True,
            "has_event_month": True,
            "observed_relative_month_count": 3,
            "expected_relative_month_count": 3,
            "observed_relative_months": (-1, 0, 1),
            "missing_relative_months": (),
        },
        {
            "strategy_id": "strat_b",
            "transition_date": pd.Timestamp("2023-03-31"),
            "from": REGIME_LABEL,
            "to": REGIME_LABEL,
            "window_status": "missing",
            "is_complete_window": False,
            "has_event_month": False,
            "observed_relative_month_count": 0,
            "expected_relative_month_count": 3,
            "observed_relative_months": (),
            "missing_relative_months": (-1, 0, 1),
        },
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
