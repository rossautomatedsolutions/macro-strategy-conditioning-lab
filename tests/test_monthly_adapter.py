from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRED_I_ADAPTER = Path(r"C:\GitHub\fred-macro-regimes-lab\scripts\run_fred_i_monthly.py")
FRED_II_ADAPTER = ROOT / "scripts" / "run_fred_ii_monthly.py"


def test_monthly_adapter_consumes_the_declared_fred_i_bundle_and_reports_source_limits(tmp_path: Path):
    fred_i_run = tmp_path / "fred-i"
    fred_ii_run = tmp_path / "fred-ii"
    fred_i = subprocess.run(
        [sys.executable, str(FRED_I_ADAPTER), "--profile", "Sandbox", "--run-dir", str(fred_i_run)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    completed = subprocess.run(
        [
            sys.executable, str(FRED_II_ADAPTER), "--profile", "Sandbox", "--run-dir", str(fred_ii_run),
            "--fred-i-run-dir", str(fred_i_run),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert fred_i.returncode == 0, fred_i.stderr
    assert completed.returncode == 0, completed.stderr
    result = json.loads((fred_ii_run / "candidate_result.json").read_text(encoding="utf-8"))
    summary = json.loads((fred_ii_run / "fred_ii_conditioning_summary.json").read_text(encoding="utf-8"))
    provenance = json.loads((fred_ii_run / "fred_ii_provenance.json").read_text(encoding="utf-8"))

    assert result["job_id"] == "fred_ii_monthly"
    assert result["status"] == "DATA_LIMITED"
    assert summary["status"] == "DATA_LIMITED"
    assert "2025-10-31" in summary["missing_regime_months"]
    assert provenance["fred_i_provenance"]["source_kind"] == "checked_in_notebook_embedded_snapshot"
