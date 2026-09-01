"""Run the governed FRED II macro-conditioning validation from a FRED I bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.data.loaders import load_regimes, load_strategy_returns, load_transitions
from src.data.validators import audit_macro_contract, audit_transition_coverage, run_all_validations


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_result(run_dir: Path, profile: str, status: str, message: str, **extra: object) -> None:
    payload = {
        "job_id": "fred_ii_monthly",
        "profile": profile,
        "status": status,
        "message": message,
        "finished_at_utc": utc_now(),
        **extra,
    }
    (run_dir / "candidate_result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def data_limited(run_dir: Path, profile: str, message: str) -> int:
    summary = {"schema_version": "1.0", "status": "DATA_LIMITED", "message": message, "generated_at_utc": utc_now()}
    (run_dir / "fred_ii_conditioning_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_result(run_dir, profile, "DATA_LIMITED", message)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=["Main", "Sandbox", "Recovery"])
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--fred-i-run-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    regimes_path = args.fred_i_run_dir / "fred_i_regimes.csv"
    transitions_path = args.fred_i_run_dir / "fred_i_transitions.csv"
    provenance_path = args.fred_i_run_dir / "fred_i_provenance.json"
    if not all(path.is_file() for path in (regimes_path, transitions_path, provenance_path)):
        return data_limited(args.run_dir, args.profile, "FRED I output bundle is absent; no macro-conditioning run was attempted.")
    try:
        fred_i_provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        regimes = load_regimes(regimes_path)
        transitions = load_transitions(transitions_path)
        strategy_path = REPO_ROOT / "data" / "strategies" / "strategy_returns_example.csv"
        strategy_returns = load_strategy_returns(strategy_path)
        run_all_validations(regimes, transitions, strategy_returns)
        macro_audit = audit_macro_contract(regimes, transitions)
        coverage = audit_transition_coverage(transitions, strategy_returns)
        summary = {
            "schema_version": "1.0",
            "conditioning_mode": "descriptive_macro_context_validation",
            "fred_i_run_dir": str(args.fred_i_run_dir),
            "fred_i_regimes_sha256": sha256(regimes_path),
            "fred_i_transitions_sha256": sha256(transitions_path),
            "fred_i_provenance_sha256": sha256(provenance_path),
            "source_max_date": fred_i_provenance.get("source_max_date"),
            "regime_row_count": len(regimes),
            "transition_row_count": len(transitions),
            "missing_regime_months": [value.strftime("%Y-%m-%d") for value in macro_audit.missing_regime_months],
            "aligned_transition_count": len(coverage.aligned),
            "outside_strategy_coverage_transition_count": len(coverage.outside_coverage),
            "generated_at_utc": utc_now(),
        }
        status = "DATA_LIMITED"
        summary["status"] = status
        summary["message"] = (
            "FRED II validated the preserved FRED I bundle, but missing monthly observations mean the result is data-limited."
            if summary["missing_regime_months"]
            else "FRED II validated the preserved FRED I bundle; live-current FRED freshness remains unproven."
        )
        (args.run_dir / "fred_ii_conditioning_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        (args.run_dir / "fred_ii_provenance.json").write_text(
            json.dumps({"schema_version": "1.0", "fred_i_provenance": fred_i_provenance, "generated_at_utc": utc_now()}, indent=2) + "\n",
            encoding="utf-8",
        )
        write_result(args.run_dir, args.profile, status, summary["message"], source_max_date=summary["source_max_date"])
        return 0
    except Exception as exc:
        write_result(args.run_dir, args.profile, "FAIL", f"FRED II adapter failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
