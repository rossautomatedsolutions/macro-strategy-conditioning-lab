"""Smoke-check the real macro data contract against data/macro inputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import audit_transition_coverage, run_all_validations


def _resolve_input(
    provided: Path | None,
    expected: Path,
    fallback: Path,
    label: str,
) -> tuple[Path, str]:
    if provided is not None:
        if not provided.exists():
            raise FileNotFoundError(f"explicit {label} file does not exist: {provided}")
        return provided, "explicit"

    if expected.exists():
        return expected, "expected"
    if fallback.exists():
        return fallback, "fallback"
    raise FileNotFoundError(f"expected {label} file does not exist: {expected}; fallback not found: {fallback}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regimes", type=Path, default=None)
    parser.add_argument("--transitions", type=Path, default=None)
    parser.add_argument(
        "--strategy",
        type=Path,
        default=Path("data/strategies/strategy_returns_example.csv"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    regimes_path, regimes_source = _resolve_input(
        args.regimes,
        Path("data/macro/regimes.csv"),
        Path("data/macro/regimes_example.csv"),
        "regimes",
    )
    transitions_path, transitions_source = _resolve_input(
        args.transitions,
        Path("data/macro/transitions.csv"),
        Path("data/macro/transitions_example.csv"),
        "transitions",
    )

    regimes = load_regimes(regimes_path)
    transitions = load_transitions(transitions_path)
    strategy_returns = load_strategy_returns(args.strategy)

    run_all_validations(regimes, transitions, strategy_returns)
    coverage = audit_transition_coverage(transitions, strategy_returns)

    macro_min = regimes["DATE"].min().date()
    macro_max = regimes["DATE"].max().date()
    regime_categories = regimes["Macro_Regime"].nunique()

    if "fallback" in {regimes_source, transitions_source}:
        print("macro input source: fallback example files")
    elif "explicit" in {regimes_source, transitions_source}:
        print("macro input source: explicit user-provided files")
    else:
        print("macro input source: expected real files")

    print(f"regimes file: {regimes_path}")
    print(f"regimes source: {regimes_source}")
    print(f"transitions file: {transitions_path}")
    print(f"transitions source: {transitions_source}")
    print(f"strategy file: {args.strategy}")
    print(f"regime row count: {len(regimes)}")
    print(f"transition row count: {len(transitions)}")
    print(f"macro date range: {macro_min} to {macro_max}")
    print(f"Macro_Regime categories: {regime_categories}")
    print(f"transition rows aligned to strategy coverage: {len(coverage.aligned)}")
    print(f"transition rows outside strategy coverage: {len(coverage.outside_coverage)}")

    if not coverage.outside_coverage.empty:
        outside_dates = ", ".join(coverage.outside_coverage["transition_date"].dt.strftime("%Y-%m-%d"))
        print(f"outside coverage transition dates: {outside_dates}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - command-line failure path
        print(f"contract failure: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
