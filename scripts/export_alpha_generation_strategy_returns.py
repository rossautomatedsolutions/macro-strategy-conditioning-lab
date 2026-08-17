"""Export Alpha Generation period returns to the FRED II strategy contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.data.alpha_generation_adapter import export_alpha_generation_period_returns


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Alpha Generation period_returns CSV.")
    parser.add_argument("--output", type=Path, required=True, help="Destination FRED II-native strategy CSV.")
    parser.add_argument(
        "--provenance-json",
        type=Path,
        default=None,
        help="Optional destination for a JSON provenance sidecar. Defaults beside --output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = export_alpha_generation_period_returns(
        source_path=args.input,
        output_path=args.output,
        provenance_path=args.provenance_json,
    )

    print(f"source file: {result.provenance['source_file']}")
    print(f"output file: {result.provenance['output_file']}")
    print(f"provenance file: {result.provenance['provenance_file']}")
    print(f"source rows: {result.provenance['source_row_count']}")
    print(f"export rows: {result.provenance['export_row_count']}")
    print(f"strategy count: {result.provenance['strategy_count']}")
    print(
        "raw entry date range: "
        f"{result.provenance['raw_entry_date_min']} to {result.provenance['raw_entry_date_max']}"
    )
    print(
        "normalized DATE range: "
        f"{result.provenance['normalized_date_min']} to {result.provenance['normalized_date_max']}"
    )
    print(
        "raw non-calendar-month-end entry dates: "
        f"{result.provenance['raw_non_calendar_month_end_entry_count']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - command-line failure path
        print(f"export failure: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
