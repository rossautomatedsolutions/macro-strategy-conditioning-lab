"""Export Part I macro regime inputs from embedded source notebook outputs.

This is a narrow handoff utility for the Part II contract audit. It rebuilds
the executed Part I monthly macro table from the embedded Plotly arrays stored
inside the source repo's Notebook 06v2, then derives the locked regime and
transition tables using the original Part I regime logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


SERIES_BY_OUTPUT_INDEX = {
    0: "CPI_YoY",
    1: "CPI_MoM",
    2: "GDP_YoY",
    3: "UNRATE",
    4: "FEDFUNDS",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-repo",
        type=Path,
        default=Path(r"C:\GitHub\fred-macro-regimes-lab"),
        help="Path to the Part I source repository.",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("data/macro"),
        help="Directory where regimes.csv and transitions.csv should be written.",
    )
    return parser.parse_args()


def load_notebook(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_dashboard_table(source_repo: Path) -> pd.DataFrame:
    notebook_path = source_repo / "notebooks" / "Notebook 06v2 - Fully Built Macro Research Pipeline.ipynb"
    notebook = load_notebook(notebook_path)
    outputs = notebook["cells"][6]["outputs"]

    first_trace = outputs[0]["data"]["application/vnd.plotly.v1+json"]["data"][0]
    dates = pd.to_datetime(first_trace["x"])
    dash = pd.DataFrame(index=dates)

    for output_idx, column in SERIES_BY_OUTPUT_INDEX.items():
        trace = outputs[output_idx]["data"]["application/vnd.plotly.v1+json"]["data"][0]
        dash[column] = trace["y"]

    return dash


def derive_part1_outputs(source_repo: Path, dash: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sys.path.append(str(source_repo))
    from macro_utils.regimes import build_macro_regimes, detect_transitions

    dash = build_macro_regimes(dash)

    regimes = (
        dash.reset_index()
        .rename(columns={"index": "DATE"})[
            ["DATE", "Growth_Regime", "Inflation_Regime", "Policy_Regime", "Macro_Regime"]
        ]
        .copy()
    )

    transitions = (
        detect_transitions(dash["Macro_Regime"])
        .rename(columns={"date": "transition_date"})[
            ["transition_date", "from", "to"]
        ]
        .copy()
    )
    return regimes, transitions


def main() -> None:
    args = parse_args()
    dash = extract_dashboard_table(args.source_repo)
    regimes, transitions = derive_part1_outputs(args.source_repo, dash)

    args.target_dir.mkdir(parents=True, exist_ok=True)
    regimes_path = args.target_dir / "regimes.csv"
    transitions_path = args.target_dir / "transitions.csv"

    regimes.to_csv(regimes_path, index=False)
    transitions.to_csv(transitions_path, index=False)

    print(f"source notebook: {args.source_repo / 'notebooks' / 'Notebook 06v2 - Fully Built Macro Research Pipeline.ipynb'}")
    print("source embedded series columns: DATE, CPI_YoY, CPI_MoM, GDP_YoY, UNRATE, FEDFUNDS")
    print(f"wrote regimes: {regimes_path} ({len(regimes)} rows)")
    print(f"wrote transitions: {transitions_path} ({len(transitions)} rows)")


if __name__ == "__main__":
    main()
