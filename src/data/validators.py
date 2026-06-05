"""Schema and integrity validation for macro and strategy inputs."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

GROWTH_ALLOWED = {"Expansion", "Contraction"}
INFL_ALLOWED = {"Inflationary", "Disinflationary"}
POLICY_ALLOWED = {"Tightening", "Easing"}


@dataclass(frozen=True)
class TransitionCoverageReport:
    """Transition rows split by whether strategy history covers the event month."""

    aligned: pd.DataFrame
    outside_coverage: pd.DataFrame


def _ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _ensure_month_end(values: pd.Series, name: str) -> None:
    bad_dates = values.loc[~values.dt.is_month_end]
    if not bad_dates.empty:
        preview = ", ".join(bad_dates.dt.strftime("%Y-%m-%d").head(5))
        raise ValueError(f"{name} must contain only month-end dates. examples: {preview}")


def _build_macro_regime_labels(regimes: pd.DataFrame) -> pd.Series:
    return (
        regimes["Growth_Regime"]
        + " / "
        + regimes["Inflation_Regime"]
        + " / "
        + regimes["Policy_Regime"]
    )


def validate_regimes(regimes: pd.DataFrame) -> None:
    """Validate macro regimes table against the locked interface."""
    required = ["DATE", "Growth_Regime", "Inflation_Regime", "Policy_Regime", "Macro_Regime"]
    _ensure_columns(regimes, required, "regimes")

    if regimes[required].isna().any().any():
        raise ValueError("regimes contains missing values in required columns")

    if regimes["DATE"].duplicated().any():
        raise ValueError("regimes must have exactly one row per DATE")

    _ensure_month_end(regimes["DATE"], "regimes.DATE")

    if not set(regimes["Growth_Regime"]).issubset(GROWTH_ALLOWED):
        raise ValueError("Growth_Regime includes invalid values")
    if not set(regimes["Inflation_Regime"]).issubset(INFL_ALLOWED):
        raise ValueError("Inflation_Regime includes invalid values")
    if not set(regimes["Policy_Regime"]).issubset(POLICY_ALLOWED):
        raise ValueError("Policy_Regime includes invalid values")

    expected = _build_macro_regime_labels(regimes)
    mismatched = regimes.loc[regimes["Macro_Regime"] != expected, ["DATE", "Macro_Regime"]].copy()
    if not mismatched.empty:
        first_idx = mismatched.index[0]
        actual = regimes.loc[first_idx, "Macro_Regime"]
        wanted = expected.loc[first_idx]
        date = regimes.loc[first_idx, "DATE"].date()
        raise ValueError(
            "Macro_Regime must equal '<Growth_Regime> / <Inflation_Regime> / <Policy_Regime>'. "
            f"example mismatch at {date}: expected '{wanted}', got '{actual}'"
        )


def validate_transitions(transitions: pd.DataFrame, regimes: pd.DataFrame) -> None:
    """Validate transition events are consistent with available regime labels and dates."""
    required = ["transition_date", "from", "to"]
    _ensure_columns(transitions, required, "transitions")

    if transitions[required].isna().any().any():
        raise ValueError("transitions contains missing values")

    _ensure_month_end(transitions["transition_date"], "transitions.transition_date")

    valid_labels = set(regimes["Macro_Regime"])
    invalid_from = set(transitions["from"]) - valid_labels
    invalid_to = set(transitions["to"]) - valid_labels
    if invalid_from or invalid_to:
        raise ValueError(
            f"transitions reference unknown regime labels. from={sorted(invalid_from)}, to={sorted(invalid_to)}"
        )

    if not set(transitions["transition_date"]).issubset(set(regimes["DATE"])):
        raise ValueError("all transition_date values must exist in regimes.DATE")


def audit_transition_coverage(
    transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
) -> TransitionCoverageReport:
    """Report which transition rows are and are not covered by strategy history."""
    strategy_dates = set(strategy_returns["DATE"])
    aligned_mask = transitions["transition_date"].isin(strategy_dates)
    aligned = transitions.loc[aligned_mask].copy().reset_index(drop=True)
    outside_coverage = transitions.loc[~aligned_mask].copy().reset_index(drop=True)
    return TransitionCoverageReport(aligned=aligned, outside_coverage=outside_coverage)


def validate_strategy_returns(strategy_returns: pd.DataFrame, regimes: pd.DataFrame) -> None:
    """Validate strategy return schema and alignment with macro timeline."""
    required = ["DATE", "strategy_id", "returns"]
    _ensure_columns(strategy_returns, required, "strategy_returns")

    if strategy_returns[required].isna().any().any():
        raise ValueError("strategy_returns contains missing values in required columns")

    if strategy_returns.duplicated(subset=["DATE", "strategy_id"]).any():
        raise ValueError("strategy_returns must have at most one row per DATE and strategy_id")

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
