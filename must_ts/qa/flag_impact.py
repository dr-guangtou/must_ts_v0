"""Evaluate candidate flag impact on a reference-selected sample."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from must_ts.catalogs.footprints import Footprint
from must_ts.catalogs.readers import read_catalog_partitions
from must_ts.catalogs.registry import CatalogContract
from must_ts.recipes.evaluator import as_boolean_mask


@dataclass(frozen=True)
class FlagGroup:
    """Named group of boolean flag columns."""

    name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class FlagImpactConfig:
    """Flag-impact configuration loaded from YAML."""

    name: str
    description: str
    flag_groups: tuple[FlagGroup, ...]

    @property
    def flag_columns(self) -> tuple[str, ...]:
        columns: list[str] = []
        for group in self.flag_groups:
            columns.extend(group.columns)
        return tuple(dict.fromkeys(columns))

    @classmethod
    def from_yaml(cls, path: Path) -> "FlagImpactConfig":
        with path.open() as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"flag-impact YAML must contain a mapping: {path}")
        return cls(
            name=str(data["name"]),
            description=str(data.get("description", "")),
            flag_groups=tuple(
                FlagGroup(name=str(group["name"]), columns=tuple(group.get("columns", [])))
                for group in data.get("flag_groups", [])
            ),
        )


@dataclass(frozen=True)
class FlagImpactResult:
    """Flag-impact result tables and summary."""

    joined_reference_photometry: pd.DataFrame
    per_flag: pd.DataFrame
    per_group: pd.DataFrame
    summary: dict[str, Any]


def evaluate_reference_flag_impact(
    *,
    photometric_contract: CatalogContract,
    reference_selection_path: Path,
    flag_config: FlagImpactConfig,
    footprint: Footprint,
    tract_ids: list[int] | None = None,
    max_partitions: int | None = None,
) -> FlagImpactResult:
    """Measure how often candidate flags affect reference-selected objects."""
    reference_df = pd.read_parquet(
        reference_selection_path, columns=[photometric_contract.object_id_column]
    )
    photometry_df = read_catalog_partitions(
        photometric_contract,
        columns=[
            photometric_contract.object_id_column,
            photometric_contract.ra_column,
            photometric_contract.dec_column,
            *flag_config.flag_columns,
        ],
        footprint=footprint,
        tract_ids=tract_ids,
        max_partitions=max_partitions,
    )
    joined_df = reference_df.merge(
        photometry_df,
        on=photometric_contract.object_id_column,
        how="inner",
        validate="one_to_one",
    )
    per_flag = _build_per_flag_table(joined_df, flag_config.flag_columns)
    per_group = _build_per_group_table(joined_df, flag_config.flag_groups)
    summary = {
        "flag_config": flag_config.name,
        "footprint": footprint.name,
        "reference_selection_path": str(reference_selection_path),
        "reference_row_count": int(len(reference_df)),
        "joined_row_count": int(len(joined_df)),
        "missing_photometry_row_count": int(len(reference_df) - len(joined_df)),
        "any_candidate_flagged_count": int(
            _flag_matrix(joined_df, flag_config.flag_columns).any(axis=1).sum()
        ),
    }
    summary["any_candidate_flagged_fraction"] = _fraction(
        summary["any_candidate_flagged_count"],
        summary["joined_row_count"],
    )
    return FlagImpactResult(
        joined_reference_photometry=joined_df,
        per_flag=per_flag,
        per_group=per_group,
        summary=summary,
    )


def write_flag_impact_result(
    *,
    result: FlagImpactResult,
    output_root: Path,
    run_name: str,
    repo_root: Path,
) -> Path:
    """Write flag-impact QA tables outside the repository."""
    run_root = output_root / "qa" / "reference_flag_impact" / run_name
    _reject_repo_local_output_root(run_root, repo_root=repo_root)
    (run_root / "tables").mkdir(parents=True, exist_ok=True)
    result.per_flag.to_csv(run_root / "tables" / "per_flag.csv", index=False)
    result.per_group.to_csv(run_root / "tables" / "per_group.csv", index=False)
    result.joined_reference_photometry.to_parquet(
        run_root / "reference_flag_columns.parquet",
        index=False,
    )
    (run_root / "summary.json").write_text(
        json.dumps(result.summary, indent=2, sort_keys=True) + "\n"
    )
    return run_root


def _build_per_flag_table(df: pd.DataFrame, flag_columns: tuple[str, ...]) -> pd.DataFrame:
    total_count = len(df)
    rows = []
    for column in flag_columns:
        flag_values = _as_boolean(df[column])
        flagged_count = int(flag_values.sum())
        rows.append(
            {
                "flag_column": column,
                "flagged_count": flagged_count,
                "total_count": total_count,
                "flagged_fraction": _fraction(flagged_count, total_count),
            }
        )
    return pd.DataFrame(rows)


def _build_per_group_table(df: pd.DataFrame, flag_groups: tuple[FlagGroup, ...]) -> pd.DataFrame:
    total_count = len(df)
    rows = []
    for group in flag_groups:
        group_matrix = _flag_matrix(df, group.columns)
        flagged_count = int(group_matrix.any(axis=1).sum())
        rows.append(
            {
                "flag_group": group.name,
                "flagged_count": flagged_count,
                "total_count": total_count,
                "flagged_fraction": _fraction(flagged_count, total_count),
                "column_count": len(group.columns),
            }
        )
    return pd.DataFrame(rows)


def _flag_matrix(df: pd.DataFrame, flag_columns: tuple[str, ...]) -> pd.DataFrame:
    return pd.DataFrame({column: _as_boolean(df[column]) for column in flag_columns})


def _as_boolean(series: pd.Series) -> pd.Series:
    return as_boolean_mask(series)


def _fraction(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _reject_repo_local_output_root(output_root: Path, *, repo_root: Path) -> None:
    resolved_output = output_root.resolve(strict=False)
    resolved_repo = repo_root.resolve(strict=False)
    if resolved_output == resolved_repo or resolved_repo in resolved_output.parents:
        raise ValueError("flag-impact output_root must be outside the repository")
