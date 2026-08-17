"""Schema and integrity validation for macro and strategy inputs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

GROWTH_ALLOWED = {"Expansion", "Contraction"}
INFL_ALLOWED = {"Inflationary", "Disinflationary"}
POLICY_ALLOWED = {"Tightening", "Easing"}


@dataclass(frozen=True)
class TransitionCoverageReport:
    """Transition rows split by whether strategy history covers the event month."""

    aligned: pd.DataFrame
    outside_coverage: pd.DataFrame


@dataclass(frozen=True)
class MacroContractAudit:
    """Audit details for macro calendar continuity and transition consistency."""

    expected_regime_month_count: int
    missing_regime_months: pd.DatetimeIndex
    duplicate_regime_months: pd.DatetimeIndex
    regime_dates_sorted: bool
    transition_dates_missing_from_regimes: pd.DatetimeIndex
    transition_label_mismatches: pd.DataFrame


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

    if transitions["transition_date"].duplicated().any():
        raise ValueError("transitions must have at most one row per transition_date")

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

    audit = audit_macro_contract(regimes, transitions)
    if not audit.transition_label_mismatches.empty:
        first = audit.transition_label_mismatches.iloc[0]
        date = first["transition_date"].date()
        raise ValueError(
            "transitions must match the realized regime sequence. "
            f"example mismatch at {date}: expected "
            f"from='{first['expected_from']}' to='{first['expected_to']}', got "
            f"from='{first['from']}' to='{first['to']}'"
        )


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

    _ensure_month_end(strategy_returns["DATE"], "strategy_returns.DATE")

    numeric_returns = pd.to_numeric(strategy_returns["returns"], errors="coerce")
    if numeric_returns.isna().any():
        preview = ", ".join(map(str, strategy_returns.loc[numeric_returns.isna(), "returns"].head(5).tolist()))
        raise ValueError(f"strategy_returns.returns must contain numeric values. examples: {preview}")
    if not np.isfinite(numeric_returns).all():
        raise ValueError("strategy_returns.returns must contain only finite numeric values")

    macro_dates = set(regimes["DATE"])
    bad_dates = sorted(set(strategy_returns["DATE"]) - macro_dates)
    if bad_dates:
        preview = ", ".join(str(d.date()) for d in bad_dates[:5])
        raise ValueError(f"strategy_returns contains dates not in macro regimes. examples: {preview}")


def audit_macro_contract(regimes: pd.DataFrame, transitions: pd.DataFrame) -> MacroContractAudit:
    """Summarize internal month-end cadence and transition consistency."""
    regime_dates = pd.DatetimeIndex(regimes["DATE"])
    expected_regime_dates = pd.date_range(regime_dates.min(), regime_dates.max(), freq="ME")
    regime_labels = regimes.sort_values("DATE").set_index("DATE")["Macro_Regime"]
    previous_labels = regime_labels.shift(1)

    mismatches: list[dict[str, object]] = []
    for _, row in transitions.sort_values("transition_date").iterrows():
        transition_date = row["transition_date"]
        if transition_date not in regime_labels.index:
            continue
        expected_from = previous_labels.loc[transition_date]
        expected_to = regime_labels.loc[transition_date]
        if row["from"] != expected_from or row["to"] != expected_to:
            mismatches.append(
                {
                    "transition_date": transition_date,
                    "from": row["from"],
                    "to": row["to"],
                    "expected_from": expected_from,
                    "expected_to": expected_to,
                }
            )

    duplicate_months = pd.DatetimeIndex(regimes.loc[regimes["DATE"].duplicated(), "DATE"].sort_values().unique())
    transition_dates_missing = pd.DatetimeIndex(
        sorted(set(transitions["transition_date"]) - set(regime_dates))
    )

    return MacroContractAudit(
        expected_regime_month_count=len(expected_regime_dates),
        missing_regime_months=expected_regime_dates.difference(regime_dates),
        duplicate_regime_months=duplicate_months,
        regime_dates_sorted=bool(regimes["DATE"].is_monotonic_increasing),
        transition_dates_missing_from_regimes=transition_dates_missing,
        transition_label_mismatches=pd.DataFrame(
            mismatches,
            columns=["transition_date", "from", "to", "expected_from", "expected_to"],
        ),
    )


def run_all_validations(
    regimes: pd.DataFrame,
    transitions: pd.DataFrame,
    strategy_returns: pd.DataFrame,
) -> None:
    """Run all project-level validation checks."""
    validate_regimes(regimes)
    validate_transitions(transitions, regimes)
    validate_strategy_returns(strategy_returns, regimes)
