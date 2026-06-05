import subprocess
import sys
from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "smoke_real_macro_contract.py"


def seed_example_inputs(tmp_path: Path) -> Path:
    macro_dir = tmp_path / "data" / "macro"
    strategy_dir = tmp_path / "data" / "strategies"
    macro_dir.mkdir(parents=True, exist_ok=True)
    strategy_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(REPO_ROOT / "data" / "macro" / "regimes_example.csv", macro_dir / "regimes_example.csv")
    shutil.copy2(REPO_ROOT / "data" / "macro" / "transitions_example.csv", macro_dir / "transitions_example.csv")
    shutil.copy2(
        REPO_ROOT / "data" / "strategies" / "strategy_returns_example.csv",
        strategy_dir / "strategy_returns_example.csv",
    )
    return tmp_path


def run_smoke(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_default_fallback_still_works(tmp_path: Path):
    result = run_smoke(cwd=seed_example_inputs(tmp_path))

    assert result.returncode == 0
    assert "macro input source: fallback example files" in result.stdout
    assert "regimes source: fallback" in result.stdout
    assert "transitions source: fallback" in result.stdout


def test_explicit_missing_regime_file_fails(tmp_path: Path):
    result = run_smoke("--regimes", "data/macro/regimes.csv", cwd=seed_example_inputs(tmp_path))

    assert result.returncode != 0
    assert "explicit regimes file does not exist: data\\macro\\regimes.csv" in result.stderr


def test_explicit_missing_transition_file_fails(tmp_path: Path):
    result = run_smoke("--transitions", "data/macro/transitions.csv", cwd=seed_example_inputs(tmp_path))

    assert result.returncode != 0
    assert "explicit transitions file does not exist: data\\macro\\transitions.csv" in result.stderr


def test_explicit_existing_files_do_not_fall_back(tmp_path: Path):
    result = run_smoke(
        "--regimes",
        "data/macro/regimes_example.csv",
        "--transitions",
        "data/macro/transitions_example.csv",
        cwd=seed_example_inputs(tmp_path),
    )

    assert result.returncode == 0
    assert "macro input source: explicit user-provided files" in result.stdout
    assert "regimes source: explicit" in result.stdout
    assert "transitions source: explicit" in result.stdout
    assert "fallback example files" not in result.stdout
