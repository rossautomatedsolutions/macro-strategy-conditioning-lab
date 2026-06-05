import pandas as pd
import pytest

from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import (
    audit_transition_coverage,
    run_all_validations,
    validate_regimes,
    validate_strategy_returns,
    validate_transitions,
)


def load_examples():
    regimes = load_regimes("data/macro/regimes_example.csv")
    transitions = load_transitions("data/macro/transitions_example.csv")
    strategy_returns = load_strategy_returns("data/strategies/strategy_returns_example.csv")
    return regimes, transitions, strategy_returns


def test_run_all_validations_passes_on_examples():
    regimes, transitions, strategy_returns = load_examples()
    run_all_validations(regimes, transitions, strategy_returns)


def test_invalid_growth_regime_raises():
    regimes, _, _ = load_examples()
    bad = regimes.copy()
    bad.loc[0, "Growth_Regime"] = "Boom"

    with pytest.raises(ValueError, match="Growth_Regime includes invalid values"):
        validate_regimes(bad)


def test_invalid_inflation_regime_raises():
    regimes, _, _ = load_examples()
    bad = regimes.copy()
    bad.loc[0, "Inflation_Regime"] = "Sticky"

    with pytest.raises(ValueError, match="Inflation_Regime includes invalid values"):
        validate_regimes(bad)


def test_invalid_policy_regime_raises():
    regimes, _, _ = load_examples()
    bad = regimes.copy()
    bad.loc[0, "Policy_Regime"] = "Neutral"

    with pytest.raises(ValueError, match="Policy_Regime includes invalid values"):
        validate_regimes(bad)


def test_missing_required_regime_column_raises():
    regimes, _, _ = load_examples()
    bad = regimes.drop(columns=["Macro_Regime"])

    with pytest.raises(ValueError, match="regimes is missing required columns"):
        validate_regimes(bad)


def test_missing_required_transition_column_raises():
    regimes, transitions, _ = load_examples()
    bad = transitions.drop(columns=["to"])

    with pytest.raises(ValueError, match="transitions is missing required columns"):
        validate_transitions(bad, regimes)


def test_missing_required_strategy_column_raises():
    regimes, _, strategy_returns = load_examples()
    bad = strategy_returns.drop(columns=["returns"])

    with pytest.raises(ValueError, match="strategy_returns is missing required columns"):
        validate_strategy_returns(bad, regimes)


def test_missing_values_in_regime_required_fields_raise():
    regimes, _, _ = load_examples()
    bad = regimes.copy()
    bad.loc[0, "Macro_Regime"] = None

    with pytest.raises(ValueError, match="regimes contains missing values"):
        validate_regimes(bad)


def test_missing_values_in_transition_required_fields_raise():
    regimes, transitions, _ = load_examples()
    bad = transitions.copy()
    bad.loc[0, "from"] = None

    with pytest.raises(ValueError, match="transitions contains missing values"):
        validate_transitions(bad, regimes)


def test_missing_values_in_strategy_required_fields_raise():
    regimes, _, strategy_returns = load_examples()
    bad = strategy_returns.copy()
    bad.loc[0, "returns"] = None

    with pytest.raises(ValueError, match="strategy_returns contains missing values"):
        validate_strategy_returns(bad, regimes)


def test_duplicate_regime_dates_raise():
    regimes, _, _ = load_examples()
    bad = pd.concat([regimes, regimes.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="exactly one row per DATE"):
        validate_regimes(bad)


def test_macro_regime_composite_label_mismatch_raises():
    regimes, _, _ = load_examples()
    bad = regimes.copy()
    bad.loc[0, "Macro_Regime"] = "Expansion / Inflationary / Easing"

    with pytest.raises(ValueError, match="Macro_Regime must equal"):
        validate_regimes(bad)


def test_regime_date_must_be_month_end():
    regimes, _, _ = load_examples()
    bad = regimes.copy()
    bad.loc[0, "DATE"] = pd.Timestamp("2023-01-30")

    with pytest.raises(ValueError, match="month-end dates"):
        validate_regimes(bad)


def test_transition_date_not_in_regimes_raises():
    regimes, transitions, _ = load_examples()
    bad = transitions.copy()
    bad.loc[0, "transition_date"] = pd.Timestamp("2022-12-31")

    with pytest.raises(ValueError, match="transition_date values must exist in regimes.DATE"):
        validate_transitions(bad, regimes)


def test_invalid_transition_labels_raise():
    regimes, transitions, _ = load_examples()
    bad = transitions.copy()
    bad.loc[0, "from"] = "Unknown / Unknown / Unknown"

    with pytest.raises(ValueError, match="transitions reference unknown regime labels"):
        validate_transitions(bad, regimes)


def test_transition_date_must_be_month_end():
    regimes, transitions, _ = load_examples()
    bad = transitions.copy()
    bad.loc[0, "transition_date"] = pd.Timestamp("2023-03-30")

    with pytest.raises(ValueError, match="month-end dates"):
        validate_transitions(bad, regimes)


def test_duplicate_strategy_date_and_id_raise():
    regimes, _, strategy_returns = load_examples()
    bad = pd.concat([strategy_returns, strategy_returns.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="at most one row per DATE and strategy_id"):
        validate_strategy_returns(bad, regimes)


def test_strategy_dates_not_fully_covered_by_macro_regimes_raise():
    regimes, _, strategy_returns = load_examples()
    bad = strategy_returns.copy()
    bad.loc[0, "DATE"] = pd.Timestamp("2022-12-31")

    with pytest.raises(ValueError, match="dates not in macro regimes"):
        validate_strategy_returns(bad, regimes)


def test_partial_strategy_history_after_macro_start_is_valid():
    regimes, transitions, strategy_returns = load_examples()
    late_start = strategy_returns.loc[strategy_returns["DATE"] >= pd.Timestamp("2023-03-31")].reset_index(drop=True)

    run_all_validations(regimes, transitions, late_start)


def test_transition_outside_strategy_coverage_is_reported_not_fatal():
    regimes, transitions, strategy_returns = load_examples()
    late_start = strategy_returns.loc[strategy_returns["DATE"] >= pd.Timestamp("2023-04-30")].reset_index(drop=True)

    run_all_validations(regimes, transitions, late_start)
    coverage = audit_transition_coverage(transitions, late_start)

    assert coverage.aligned["transition_date"].tolist() == [
        pd.Timestamp("2023-04-30"),
        pd.Timestamp("2023-05-31"),
        pd.Timestamp("2023-06-30"),
    ]
    assert coverage.outside_coverage["transition_date"].tolist() == [pd.Timestamp("2023-03-31")]
