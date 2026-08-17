import pandas as pd

from src.conditioning.transition_analysis import (
    build_transition_window_diagnostics,
    build_transition_windows,
    cumulative_transition_profile,
    summarize_transition_windows,
)


def build_joined_sample(dates: list[str] | None = None) -> pd.DataFrame:
    date_values = pd.to_datetime(
        dates
        or [
            "2023-01-31",
            "2023-02-28",
            "2023-03-31",
            "2023-04-30",
            "2023-05-31",
        ]
    )
    repeated_dates = list(date_values) * 2
    return pd.DataFrame(
        {
            "DATE": repeated_dates,
            "strategy_id": ["strat_a"] * len(date_values) + ["strat_b"] * len(date_values),
            "returns": [0.01, 0.02, -0.01, 0.03, -0.02][: len(date_values)]
            + [-0.01, 0.01, 0.00, 0.02, -0.01][: len(date_values)],
            "Macro_Regime": [
                "Expansion / Disinflationary / Easing",
                "Expansion / Disinflationary / Easing",
                "Expansion / Inflationary / Tightening",
                "Contraction / Inflationary / Tightening",
                "Contraction / Disinflationary / Easing",
            ][: len(date_values)]
            * 2,
        }
    )


def build_transition_sample(transition_dates: list[str] | None = None) -> pd.DataFrame:
    dates = transition_dates or ["2023-03-31", "2023-08-31"]
    return pd.DataFrame(
        {
            "transition_date": pd.to_datetime(dates),
            "from": [
                "Expansion / Disinflationary / Easing",
                "Contraction / Disinflationary / Easing",
            ][: len(dates)],
            "to": [
                "Expansion / Inflationary / Tightening",
                "Expansion / Disinflationary / Easing",
            ][: len(dates)],
        }
    )


def test_relative_month_calculation_is_correct_for_contiguous_months():
    joined = build_joined_sample()
    transitions = build_transition_sample(["2023-03-31"])

    windows = build_transition_windows(joined, transitions, window=2)
    strat_a = windows[windows["strategy_id"] == "strat_a"].sort_values("DATE")

    assert strat_a["relative_month"].tolist() == [-2, -1, 0, 1, 2]
    assert strat_a["window_status"].tolist() == ["complete"] * 5
    assert strat_a["is_complete_window"].tolist() == [True] * 5


def test_missing_month_before_transition_uses_calendar_offsets():
    joined = build_joined_sample(["2023-01-31", "2023-03-31", "2023-04-30"])
    transitions = build_transition_sample(["2023-03-31"])

    windows = build_transition_windows(joined, transitions, window=2)
    strat_a = windows[windows["strategy_id"] == "strat_a"].sort_values("DATE")

    assert strat_a["relative_month"].tolist() == [-2, 0, 1]
    assert strat_a["window_status"].tolist() == ["partial"] * 3
    assert strat_a["missing_relative_months"].tolist() == [(-1, 2)] * 3


def test_missing_month_after_transition_uses_calendar_offsets():
    joined = build_joined_sample(["2023-01-31", "2023-02-28", "2023-03-31", "2023-05-31"])
    transitions = build_transition_sample(["2023-03-31"])

    windows = build_transition_windows(joined, transitions, window=2)
    strat_a = windows[windows["strategy_id"] == "strat_a"].sort_values("DATE")

    assert strat_a["relative_month"].tolist() == [-2, -1, 0, 2]
    assert strat_a["window_status"].tolist() == ["partial"] * 4
    assert strat_a["missing_relative_months"].tolist() == [(1,)] * 4


def test_multiple_missing_months_are_reported_explicitly():
    joined = build_joined_sample(["2023-01-31", "2023-03-31", "2023-06-30"])
    transitions = build_transition_sample(["2023-03-31"])

    windows = build_transition_windows(joined, transitions, window=3)
    diagnostics = build_transition_window_diagnostics(windows, window=3)

    assert diagnostics.to_dict("records") == [
        {
            "strategy_id": "strat_a",
            "transition_date": pd.Timestamp("2023-03-31"),
            "from": "Expansion / Disinflationary / Easing",
            "to": "Expansion / Inflationary / Tightening",
            "window_status": "partial",
            "is_complete_window": False,
            "has_event_month": True,
            "observed_relative_month_count": 3,
            "expected_relative_month_count": 7,
            "observed_relative_months": (-2, 0, 3),
            "missing_relative_months": (-3, -1, 1, 2),
        },
        {
            "strategy_id": "strat_b",
            "transition_date": pd.Timestamp("2023-03-31"),
            "from": "Expansion / Disinflationary / Easing",
            "to": "Expansion / Inflationary / Tightening",
            "window_status": "partial",
            "is_complete_window": False,
            "has_event_month": True,
            "observed_relative_month_count": 3,
            "expected_relative_month_count": 7,
            "observed_relative_months": (-2, 0, 3),
            "missing_relative_months": (-3, -1, 1, 2),
        },
    ]


def test_transition_month_zero_exists_when_transition_month_is_present():
    joined = build_joined_sample()
    transitions = build_transition_sample(["2023-03-31"])

    windows = build_transition_windows(joined, transitions, window=2)
    assert (windows["relative_month"] == 0).any()
    assert windows.loc[windows["relative_month"] == 0, "has_event_month"].all()


def test_unsorted_input_is_sorted_and_supported():
    joined = build_joined_sample().sample(frac=1.0, random_state=7).reset_index(drop=True)
    transitions = build_transition_sample(["2023-03-31"])

    windows = build_transition_windows(joined, transitions, window=1)
    strat_a = windows[windows["strategy_id"] == "strat_a"]

    assert strat_a["DATE"].tolist() == list(pd.to_datetime(["2023-02-28", "2023-03-31", "2023-04-30"]))
    assert strat_a["relative_month"].tolist() == [-1, 0, 1]


def test_transitions_outside_available_dates_are_skipped_cleanly():
    joined = build_joined_sample()
    transitions = build_transition_sample(["2023-08-31"])

    windows = build_transition_windows(joined, transitions, window=1)
    assert windows.empty


def test_complete_only_aggregates_exclude_partial_windows():
    joined = build_joined_sample()
    transitions = build_transition_sample(["2023-01-31", "2023-03-31"])

    windows = build_transition_windows(joined, transitions, window=2)
    summary_all = summarize_transition_windows(windows)
    summary_complete_only = summarize_transition_windows(windows, complete_only=True)
    profile_complete_only = cumulative_transition_profile(windows, complete_only=True)

    assert set(windows["window_status"]) == {"complete", "partial"}
    assert summary_all.loc[summary_all["relative_month"] == 0, "obs"].max() == 2
    assert summary_complete_only["obs"].tolist() == [1] * len(summary_complete_only)
    assert sorted(summary_complete_only["relative_month"].unique().tolist()) == [-2, -1, 0, 1, 2]
    assert profile_complete_only["obs"].tolist() == [1] * len(profile_complete_only)


def test_transition_analysis_does_not_mutate_inputs():
    joined = build_joined_sample()
    transitions = build_transition_sample()
    joined_original = joined.copy(deep=True)
    transitions_original = transitions.copy(deep=True)

    windows = build_transition_windows(joined, transitions, window=1)
    summarize_transition_windows(windows)
    cumulative_transition_profile(windows)

    pd.testing.assert_frame_equal(joined, joined_original)
    pd.testing.assert_frame_equal(transitions, transitions_original)
