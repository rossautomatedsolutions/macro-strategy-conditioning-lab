"""Adapt Alpha Generation period-return artifacts to the FRED II strategy contract."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_SOURCE_COLUMNS = ["variant_id", "entry_date", "portfolio_return"]
OPTIONAL_SOURCE_COLUMNS = ["variant_name", "variant_status"]


@dataclass(frozen=True)
class AlphaGenerationExportResult:
    """Result of exporting a source artifact to the FRED II strategy contract."""

    strategy_returns: pd.DataFrame
    provenance: dict[str, Any]


def _ensure_source_columns(df: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_SOURCE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Alpha Generation source is missing required columns: {missing}")


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in companion metadata file: {path}")
    return payload


def _companion_paths(source_path: Path) -> dict[str, Path]:
    stem = source_path.stem
    if stem.endswith("_period_returns"):
        prefix = stem[: -len("_period_returns")]
        return {
            "summary_json": source_path.with_name(f"{prefix}_summary.json"),
            "run_manifest_json": source_path.with_name(f"{prefix}_run_manifest.json"),
            "review_report_md": source_path.with_name(f"{prefix}_review_report.md"),
        }
    return {}


def build_fredii_strategy_returns(source_path: str | Path) -> AlphaGenerationExportResult:
    """Return a FRED II-native strategy-return frame plus provenance metadata."""
    source_path = Path(source_path)
    source = pd.read_csv(source_path)
    _ensure_source_columns(source)

    variant_ids = source["variant_id"].astype("string").str.strip()
    if variant_ids.isna().any() or (variant_ids == "").any():
        raise ValueError("Alpha Generation source contains blank variant_id values")

    raw_entry_dates = pd.to_datetime(source["entry_date"], errors="raise")
    normalized_dates = raw_entry_dates + pd.offsets.MonthEnd(0)

    numeric_returns = pd.to_numeric(source["portfolio_return"], errors="coerce")
    if numeric_returns.isna().any():
        preview = source.loc[numeric_returns.isna(), "portfolio_return"].head(5).tolist()
        raise ValueError(f"Alpha Generation portfolio_return contains non-numeric values. examples: {preview}")
    if not np.isfinite(numeric_returns).all():
        raise ValueError("Alpha Generation portfolio_return must contain only finite numeric values")

    strategy_returns = pd.DataFrame(
        {
            "DATE": normalized_dates,
            "strategy_id": variant_ids,
            "returns": numeric_returns.astype(float),
        }
    )
    if "variant_name" in source.columns:
        strategy_names = source["variant_name"].astype("string").str.strip()
        strategy_names = strategy_names.mask(strategy_names == "", pd.NA)
        strategy_returns["strategy_name"] = strategy_names

    if strategy_returns.duplicated(subset=["DATE", "strategy_id"]).any():
        duplicates = strategy_returns.loc[
            strategy_returns.duplicated(subset=["DATE", "strategy_id"], keep=False),
            ["DATE", "strategy_id"],
        ].copy()
        duplicates["DATE"] = duplicates["DATE"].dt.strftime("%Y-%m-%d")
        preview = duplicates.drop_duplicates().head(5).to_dict("records")
        raise ValueError(
            "Alpha Generation export would create duplicate FRED II DATE/strategy_id rows "
            f"after calendar month-end normalization. examples: {preview}"
        )

    strategy_returns = strategy_returns.sort_values(["strategy_id", "DATE"]).reset_index(drop=True)

    companions = _companion_paths(source_path)
    summary_payload = _load_optional_json(companions["summary_json"]) if "summary_json" in companions else None
    run_manifest_payload = (
        _load_optional_json(companions["run_manifest_json"]) if "run_manifest_json" in companions else None
    )

    summary_excerpt: dict[str, Any] = {}
    if summary_payload is not None:
        for key in (
            "experiment_id",
            "run_classification",
            "run_kind",
            "universe_interpretation",
            "current_only_static_universe",
            "point_in_time_membership_available",
            "diagnostic_run_only",
        ):
            if key in summary_payload:
                summary_excerpt[key] = summary_payload[key]

    provenance = {
        "generator": "scripts/export_alpha_generation_strategy_returns.py",
        "source_file": str(source_path.resolve()),
        "source_sha256": sha256(source_path.read_bytes()).hexdigest(),
        "source_row_count": int(len(source)),
        "export_row_count": int(len(strategy_returns)),
        "strategy_count": int(strategy_returns["strategy_id"].nunique()),
        "raw_entry_date_min": raw_entry_dates.min().strftime("%Y-%m-%d"),
        "raw_entry_date_max": raw_entry_dates.max().strftime("%Y-%m-%d"),
        "normalized_date_min": strategy_returns["DATE"].min().strftime("%Y-%m-%d"),
        "normalized_date_max": strategy_returns["DATE"].max().strftime("%Y-%m-%d"),
        "raw_non_calendar_month_end_entry_count": int((~raw_entry_dates.dt.is_month_end).sum()),
        "strategy_ids": sorted(strategy_returns["strategy_id"].dropna().unique().tolist()),
        "mapping": {
            "DATE": "calendar month-end normalization of source entry_date",
            "strategy_id": "variant_id",
            "returns": "portfolio_return",
            "strategy_name": "variant_name when present",
        },
        "source_variant_status_counts": (
            source["variant_status"].value_counts(dropna=False).to_dict()
            if "variant_status" in source.columns
            else {}
        ),
        "companion_files": {
            name: str(path.resolve())
            for name, path in companions.items()
            if path.exists()
        },
        "source_summary": summary_excerpt,
        "source_run_manifest_detected": run_manifest_payload is not None,
    }

    return AlphaGenerationExportResult(strategy_returns=strategy_returns, provenance=provenance)


def export_alpha_generation_period_returns(
    source_path: str | Path,
    output_path: str | Path,
    provenance_path: str | Path | None = None,
) -> AlphaGenerationExportResult:
    """Write a contract CSV and JSON provenance sidecar for a source artifact."""
    result = build_fredii_strategy_returns(source_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.strategy_returns.to_csv(output_path, index=False, date_format="%Y-%m-%d")

    if provenance_path is None:
        provenance_path = output_path.with_name(f"{output_path.stem}.provenance.json")
    provenance_path = Path(provenance_path)
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(result.provenance, indent=2), encoding="utf-8")

    return AlphaGenerationExportResult(
        strategy_returns=result.strategy_returns,
        provenance={
            **result.provenance,
            "output_file": str(output_path.resolve()),
            "provenance_file": str(provenance_path.resolve()),
        },
    )
