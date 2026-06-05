import pandas as pd

from src.conditioning.transition_analysis import (
    build_transition_windows,
    cumulative_transition_profile,
    summarize_transition_windows,
)


def build_joined_sample() -> pd.DataFrame:
    dates = pd.to_datetime(
        [
            "2023-01-31",
            "2023-02-28",
            "2023-03-31",
            "2023-04-30",
            "2023-05-31",
        ]
    )
    return pd.DataFrame(
        {
            "DATE": list(dates) * 2,
            "strategy_id": ["strat_a"] * 5 + ["strat_b"] * 5,
            "returns": [0.01, 0.02, -0.01, 0.03, -0.02, -0.01, 0.01, 0.00, 0.02, -0.01],
            "Macro_Regime": [
                "Expansion / Disinflationary / Easing",
                "Expansion / Disinflationary / Easing",
                "Expansion / Inflationary / Tightening",
                "Contraction / Inflationary / Tightening",
                "Contraction / Disinflationary / Easing",
            ]
            * 2,
        }
    )


def build_transition_sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transition_date": pd.to_datetime(["2023-03-31", "2023-08-31"]),
            "from": [
                "Expansion / Disinflationary / Easing",
                "Contraction / Disinflationary / Easing",
            ],
            "to": [
                "Expansion / Inflationary / Tightening",
                "Expansion / Disinflationary / Easing",
            ],
        }
    )


def test_relative_month_calculation_is_correct():
    joined = build_joined_sample()
    transitions = build_transition_sample().iloc[[0]].copy()

    windows = build_transition_windows(joined, transitions, window=2)
    strat_a = windows[windows["strategy_id"] == "strat_a"].sort_values("DATE")

    assert strat_a["relative_month"].tolist() == [-2, -1, 0, 1, 2]


def test_transition_month_zero_exists():
    joined = build_joined_sample()
    transitions = build_transition_sample().iloc[[0]].copy()

    windows = build_transition_windows(joined, transitions, window=2)
    assert (windows["relative_month"] == 0).any()


def test_configurable_window_size_is_respected():
    joined = build_joined_sample()
    transitions = build_transition_sample().iloc[[0]].copy()

    windows = build_transition_windows(joined, transitions, window=1)
    assert sorted(windows["relative_month"].unique().tolist()) == [-1, 0, 1]


def test_strategy_id_is_preserved():
    joined = build_joined_sample()
    transitions = build_transition_sample().iloc[[0]].copy()

    windows = build_transition_windows(joined, transitions, window=1)
    assert set(windows["strategy_id"]) == {"strat_a", "strat_b"}


def test_from_to_labels_are_preserved():
    joined = build_joined_sample()
    transitions = build_transition_sample().iloc[[0]].copy()

    windows = build_transition_windows(joined, transitions, window=1)
    assert set(windows["from"]) == {"Expansion / Disinflationary / Easing"}
    assert set(windows["to"]) == {"Expansion / Inflationary / Tightening"}


def test_transitions_outside_available_dates_are_skipped_cleanly():
    joined = build_joined_sample()
    transitions = build_transition_sample().iloc[[1]].copy()

    windows = build_transition_windows(joined, transitions, window=1)
    assert windows.empty


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


def test_multiple_strategy_ids_are_supported_in_summaries():
    joined = build_joined_sample()
    transitions = build_transition_sample().iloc[[0]].copy()

    windows = build_transition_windows(joined, transitions, window=1)
    summary = summarize_transition_windows(windows)

    assert set(summary["strategy_id"]) == {"strat_a", "strat_b"}


def test_cumulative_transition_profile_returns_relative_month_summary():
    joined = build_joined_sample()
    transitions = build_transition_sample().iloc[[0]].copy()

    windows = build_transition_windows(joined, transitions, window=1)
    profile = cumulative_transition_profile(windows)

    assert {"strategy_id", "relative_month", "mean_cumulative_return", "obs"}.issubset(profile.columns)
