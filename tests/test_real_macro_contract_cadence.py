import pandas as pd

from src.data.loaders import load_regimes, load_transitions
from src.data.validators import audit_macro_contract, run_all_validations


def test_checked_in_real_macro_files_have_complete_month_end_coverage():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")

    audit = audit_macro_contract(regimes, transitions)

    assert audit.expected_regime_month_count == 420
    assert audit.missing_regime_months.empty
    assert audit.duplicate_regime_months.empty
    assert audit.regime_dates_sorted is True
    assert audit.transition_dates_missing_from_regimes.empty
    assert audit.transition_label_mismatches.empty


def test_checked_in_real_macro_files_still_validate_with_wide_sample_fixture():
    regimes = load_regimes("data/macro/regimes.csv")
    transitions = load_transitions("data/macro/transitions.csv")
    strategy_returns = pd.read_csv("data/strategies/strategy_returns_wide_sample.csv", parse_dates=["DATE"])
    strategy_returns = strategy_returns.sort_values(["strategy_id", "DATE"]).reset_index(drop=True)

    run_all_validations(regimes, transitions, strategy_returns)
