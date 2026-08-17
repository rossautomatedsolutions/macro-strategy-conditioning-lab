import json

import pandas as pd
import pytest

from src.data.alpha_generation_adapter import build_fredii_strategy_returns, export_alpha_generation_period_returns


def write_source_csv(tmp_path, rows):
    source_path = tmp_path / "phase2_experiment_001_period_returns.csv"
    pd.DataFrame(rows).to_csv(source_path, index=False)
    return source_path


def test_adapter_normalizes_trading_month_end_dates_and_writes_provenance(tmp_path):
    source_path = write_source_csv(
        tmp_path,
        [
            {
                "variant_id": "raw_momentum_top_fraction",
                "variant_name": "Raw momentum",
                "entry_date": "2025-11-28",
                "portfolio_return": "0.0125",
                "variant_status": "executed",
            },
            {
                "variant_id": "universe_equal_weight_baseline",
                "variant_name": "Baseline",
                "entry_date": "2025-10-31",
                "portfolio_return": "-0.01",
                "variant_status": "executed",
            },
        ],
    )
    (tmp_path / "phase2_experiment_001_summary.json").write_text(
        json.dumps(
            {
                "experiment_id": "PHASE2-EXP001-MEDIUM-TERM-MOMENTUM",
                "run_classification": "STATIC_CURRENT_UNIVERSE_DIAGNOSTIC",
                "run_kind": "historical_bounded_research",
            }
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "fredii_strategy_returns.csv"
    result = export_alpha_generation_period_returns(source_path, output_path)

    exported = pd.read_csv(output_path)
    assert exported.to_dict("records") == [
        {
            "DATE": "2025-11-30",
            "strategy_id": "raw_momentum_top_fraction",
            "returns": 0.0125,
            "strategy_name": "Raw momentum",
        },
        {
            "DATE": "2025-10-31",
            "strategy_id": "universe_equal_weight_baseline",
            "returns": -0.01,
            "strategy_name": "Baseline",
        },
    ]

    provenance_path = tmp_path / "fredii_strategy_returns.provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert provenance["source_row_count"] == 2
    assert provenance["export_row_count"] == 2
    assert provenance["raw_non_calendar_month_end_entry_count"] == 1
    assert provenance["source_summary"]["experiment_id"] == "PHASE2-EXP001-MEDIUM-TERM-MOMENTUM"
    assert result.provenance["output_file"] == str(output_path.resolve())


def test_adapter_fails_when_normalization_creates_duplicate_strategy_month_rows(tmp_path):
    source_path = write_source_csv(
        tmp_path,
        [
            {
                "variant_id": "raw_momentum_top_fraction",
                "entry_date": "2025-11-28",
                "portfolio_return": "0.01",
            },
            {
                "variant_id": "raw_momentum_top_fraction",
                "entry_date": "2025-11-30",
                "portfolio_return": "0.02",
            },
        ],
    )

    with pytest.raises(ValueError, match="duplicate FRED II DATE/strategy_id rows"):
        build_fredii_strategy_returns(source_path)


def test_adapter_fails_on_malformed_returns(tmp_path):
    source_path = write_source_csv(
        tmp_path,
        [
            {
                "variant_id": "raw_momentum_top_fraction",
                "entry_date": "2025-11-28",
                "portfolio_return": "bad-value",
            }
        ],
    )

    with pytest.raises(ValueError, match="portfolio_return contains non-numeric values"):
        build_fredii_strategy_returns(source_path)


def test_adapter_requires_source_columns(tmp_path):
    source_path = tmp_path / "phase2_experiment_001_period_returns.csv"
    pd.DataFrame([{"variant_id": "raw_momentum_top_fraction", "portfolio_return": 0.01}]).to_csv(
        source_path,
        index=False,
    )

    with pytest.raises(ValueError, match="missing required columns"):
        build_fredii_strategy_returns(source_path)
