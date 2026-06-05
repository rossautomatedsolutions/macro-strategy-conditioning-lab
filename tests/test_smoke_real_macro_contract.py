import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "smoke_real_macro_contract.py"


def run_smoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_default_fallback_still_works():
    result = run_smoke()

    assert result.returncode == 0
    assert "macro input source: fallback example files" in result.stdout
    assert "regimes source: fallback" in result.stdout
    assert "transitions source: fallback" in result.stdout


def test_explicit_missing_regime_file_fails():
    result = run_smoke("--regimes", "data/macro/regimes.csv")

    assert result.returncode != 0
    assert "explicit regimes file does not exist: data\\macro\\regimes.csv" in result.stderr


def test_explicit_missing_transition_file_fails():
    result = run_smoke("--transitions", "data/macro/transitions.csv")

    assert result.returncode != 0
    assert "explicit transitions file does not exist: data\\macro\\transitions.csv" in result.stderr


def test_explicit_existing_files_do_not_fall_back():
    result = run_smoke(
        "--regimes",
        "data/macro/regimes_example.csv",
        "--transitions",
        "data/macro/transitions_example.csv",
    )

    assert result.returncode == 0
    assert "macro input source: explicit user-provided files" in result.stdout
    assert "regimes source: explicit" in result.stdout
    assert "transitions source: explicit" in result.stdout
    assert "fallback example files" not in result.stdout
