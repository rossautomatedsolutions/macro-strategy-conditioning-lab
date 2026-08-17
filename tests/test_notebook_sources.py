import json
from pathlib import Path


NOTEBOOK_DIR = Path("notebooks")
EXAMPLE_NOTEBOOKS = [
    "01_inputs_validation.ipynb",
    "02_returns_by_regime.ipynb",
    "03_risk_drawdowns.ipynb",
    "04_transition_behavior.ipynb",
]
CANONICAL_NOTEBOOKS = [
    "05_cross_strategy.ipynb",
    "06_regime_robustness.ipynb",
    "07_transition_diagnostics.ipynb",
    "08_final_summary_packet.ipynb",
]


def load_notebook(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def notebook_text(path: Path) -> str:
    notebook = load_notebook(path)
    return "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])


def first_code_cell_source(path: Path) -> str:
    notebook = load_notebook(path)
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            return "".join(cell.get("source", []))
    raise AssertionError(f"{path.name} does not contain a code cell")


def test_all_notebooks_have_cell_ids_repo_bootstrap_and_no_todos():
    for path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = load_notebook(path)

        assert all(cell.get("id") for cell in notebook["cells"]), f"{path.name} is missing notebook cell ids"

        first_code_source = first_code_cell_source(path)
        assert "REPO_ROOT = _repo_root()" in first_code_source
        assert "Could not locate repository root containing 'src' and 'data'." in first_code_source

        assert "TODO:" not in notebook_text(path), f"{path.name} still contains a TODO placeholder"


def test_example_notebooks_use_example_contract_inputs():
    for name in EXAMPLE_NOTEBOOKS:
        source = first_code_cell_source(NOTEBOOK_DIR / name)
        assert 'REPO_ROOT / "data" / "macro" / "regimes_example.csv"' in source
        assert 'REPO_ROOT / "data" / "macro" / "transitions_example.csv"' in source
        assert 'REPO_ROOT / "data" / "strategies" / "strategy_returns_example.csv"' in source


def test_canonical_notebooks_use_real_macro_and_narrow_strategy_inputs():
    for name in CANONICAL_NOTEBOOKS:
        source = first_code_cell_source(NOTEBOOK_DIR / name)
        assert 'REPO_ROOT / "data" / "macro" / "regimes.csv"' in source
        assert 'REPO_ROOT / "data" / "macro" / "transitions.csv"' in source
        assert 'REPO_ROOT / "data" / "strategies" / "strategy_returns_example.csv"' in source


def test_orientation_notebook_is_an_executable_inventory_not_a_placeholder():
    source = first_code_cell_source(NOTEBOOK_DIR / "00_orientation.ipynb")

    assert "artifact_summary" in source
    assert "validation_summary" in source
    assert 'load_regimes(REPO_ROOT / "data" / "macro" / "regimes.csv")' in source
    assert 'load_strategy_returns(REPO_ROOT / "data" / "strategies" / "strategy_returns_wide_sample.csv")' in source
