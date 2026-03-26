"""Schema and integrity validation for macro and strategy inputs."""

from __future__ import annotations

import pandas as pd

GROWTH_ALLOWED = {"Expansion", "Contraction"}
INFL_ALLOWED = {"Inflationary", "Disinflationary"}
POLICY_ALLOWED = {"Tightening", "Easing"}


def _ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def validate_regimes(regimes: pd.DataFrame) -> None:
    """Validate macro regimes table against the locked interface."""
    required = ["DATE", "Growth_Regime", "Inflation_Regime", "Policy_Regime", "Macro_Regime"]
    _ensure_columns(regimes, required, "regimes")

    if regimes[required].isna().any().any():
        raise ValueError("regimes contains missing values in required columns")

    if regimes["DATE"].duplicated().any():
        raise ValueError("regimes must have exactly one row per DATE")

    if not set(regimes["Growth_Regime"]).issubset(GROWTH_ALLOWED):
        raise ValueError("Growth_Regime includes invalid values")
    if not set(regimes["Inflation_Regime"]).issubset(INFL_ALLOWED):
        raise ValueError("Inflation_Regime includes invalid values")
    if not set(regimes["Policy_Regime"]).issubset(POLICY_ALLOWED):
        raise ValueError("Policy_Regime includes invalid values")


def validate_transitions(transitions: pd.DataFrame, regimes: pd.DataFrame) -> None:
    """Validate transition events are consistent with available regime labels and dates."""
    required = ["transition_date", "from", "to"]
    _ensure_columns(transitions, required, "transitions")

    if transitions[required].isna().any().any():
        raise ValueError("transitions contains missing values")

    valid_labels = set(regimes["Macro_Regime"])
    invalid_from = set(transitions["from"]) - valid_labels
    invalid_to = set(transitions["to"]) - valid_labels
    if invalid_from or invalid_to:
        raise ValueError(
            f"transitions reference unknown regime labels. from={sorted(invalid_from)}, to={sorted(invalid_to)}"
        )

    if not set(transitions["transition_date"]).issubset(set(regimes["DATE"])):
        raise ValueError("all transition_date values must exist in regimes.DATE")


def validate_strategy_returns(strategy_returns: pd.DataFrame, regimes: pd.DataFrame) -> None:
    """Validate strategy return schema and alignment with macro timeline."""
    required = ["DATE", "strategy_id", "returns"]
    _ensure_columns(strategy_returns, required, "strategy_returns")

    if strategy_returns[required].isna().any().any():
        raise ValueError("strategy_returns contains missing values in required columns")

    macro_dates = set(regimes["DATE"])
    bad_dates = sorted(set(strategy_returns["DATE"]) - macro_dates)
    if bad_dates:
        preview = ", ".join(str(d.date()) for d in bad_dates[:5])
        raise ValueError(f"strategy_returns contains dates not in macro regimes. examples: {preview}")


def run_all_validations(
    regimes: pd.DataFrame,
    transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
) -> None:
    """Run all project-level validation checks."""
    validate_regimes(regimes)
    validate_transitions(transitions, regimes)
    validate_strategy_returns(strategy_returns, regimes)
