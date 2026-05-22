"""Reference-catalog footprint selection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml

from must_ts.catalogs.footprints import Footprint
from must_ts.catalogs.readers import read_catalog_partitions_with_summary
from must_ts.catalogs.registry import CatalogContract


@dataclass(frozen=True)
class ReferenceFootprintSelection:
    """Rows and measured counts for a reference-footprint selection."""

    dataframe: pd.DataFrame
    summary: dict[str, Any]
    spatial_partition_summary: pd.DataFrame
    reference_partition_summary: pd.DataFrame


def select_reference_catalog_in_footprint(
    *,
    reference_contract: CatalogContract,
    footprint: Footprint,
    tract_ids: Iterable[int] | None = None,
    max_partitions: int | None = None,
) -> ReferenceFootprintSelection:
    """Select reference rows inside a footprint, using a spatial source if needed."""
    if reference_contract.ra_column is not None and reference_contract.dec_column is not None:
        return _select_coordinate_bearing_reference(
            reference_contract=reference_contract,
            footprint=footprint,
            tract_ids=tract_ids,
            max_partitions=max_partitions,
        )
    if reference_contract.spatial_source is None:
        raise ValueError(
            f"reference catalog {reference_contract.name} has no RA/Dec columns and no "
            "spatial_source"
        )
    return _select_reference_with_spatial_source(
        reference_contract=reference_contract,
        footprint=footprint,
        tract_ids=tract_ids,
        max_partitions=max_partitions,
    )


def write_reference_footprint_selection(
    *,
    selection: ReferenceFootprintSelection,
    output_root: Path,
    run_name: str,
    repo_root: Path,
) -> Path:
    """Write a reference-footprint selection outside the repository."""
    run_root = output_root / "reference_footprints" / run_name
    _reject_repo_local_output_root(run_root, repo_root=repo_root)
    (run_root / "tables").mkdir(parents=True, exist_ok=True)
    selection.dataframe.to_parquet(run_root / "selected_reference.parquet", index=False)
    selection.spatial_partition_summary.to_csv(
        run_root / "tables" / "spatial_partition_summary.csv", index=False
    )
    selection.reference_partition_summary.to_csv(
        run_root / "tables" / "reference_partition_summary.csv", index=False
    )
    (run_root / "summary.json").write_text(
        json.dumps(selection.summary, indent=2, sort_keys=True) + "\n"
    )
    (run_root / "summary.yaml").write_text(yaml.safe_dump(selection.summary, sort_keys=True))
    return run_root


def _select_coordinate_bearing_reference(
    *,
    reference_contract: CatalogContract,
    footprint: Footprint,
    tract_ids: Iterable[int] | None,
    max_partitions: int | None,
) -> ReferenceFootprintSelection:
    read_result = read_catalog_partitions_with_summary(
        reference_contract,
        columns=_unique_columns(
            [
                reference_contract.object_id_column,
                reference_contract.ra_column,
                reference_contract.dec_column,
                *reference_contract.default_columns,
            ]
        ),
        footprint=footprint,
        tract_ids=tract_ids,
        max_partitions=max_partitions,
    )
    summary = _build_summary(
        reference_contract=reference_contract,
        footprint=footprint,
        spatial_parent_row_count=int(read_result.summary["input_row_count"].sum()),
        spatial_selected_row_count=int(read_result.summary["output_row_count"].sum()),
        reference_parent_row_count=int(read_result.summary["input_row_count"].sum()),
        selected_reference_row_count=len(read_result.dataframe),
    )
    return ReferenceFootprintSelection(
        dataframe=read_result.dataframe,
        summary=summary,
        spatial_partition_summary=read_result.summary,
        reference_partition_summary=read_result.summary.copy(),
    )


def _select_reference_with_spatial_source(
    *,
    reference_contract: CatalogContract,
    footprint: Footprint,
    tract_ids: Iterable[int] | None,
    max_partitions: int | None,
) -> ReferenceFootprintSelection:
    spatial_source = reference_contract.spatial_source
    if spatial_source is None:
        raise ValueError(f"reference catalog {reference_contract.name} has no spatial_source")

    spatial_read_result = read_catalog_partitions_with_summary(
        spatial_source,
        columns=_unique_columns(
            [
                spatial_source.object_id_column,
                spatial_source.ra_column,
                spatial_source.dec_column,
                *spatial_source.default_columns,
            ]
        ),
        footprint=footprint,
        tract_ids=tract_ids,
        max_partitions=max_partitions,
    )
    reference_read_result = read_catalog_partitions_with_summary(
        reference_contract,
        columns=_unique_columns(
            [
                reference_contract.object_id_column,
                *reference_contract.default_columns,
            ]
        ),
        tract_ids=tract_ids,
        max_partitions=max_partitions,
    )
    selected_df = spatial_read_result.dataframe.merge(
        reference_read_result.dataframe,
        left_on=spatial_source.object_id_column,
        right_on=reference_contract.object_id_column,
        how="inner",
        validate="one_to_one",
    )
    summary = _build_summary(
        reference_contract=reference_contract,
        footprint=footprint,
        spatial_parent_row_count=int(spatial_read_result.summary["input_row_count"].sum()),
        spatial_selected_row_count=int(spatial_read_result.summary["output_row_count"].sum()),
        reference_parent_row_count=int(reference_read_result.summary["input_row_count"].sum()),
        selected_reference_row_count=len(selected_df),
    )
    if "z_best" in selected_df.columns:
        summary["finite_z_best_row_count"] = int(
            pd.to_numeric(selected_df["z_best"], errors="coerce").notna().sum()
        )
    return ReferenceFootprintSelection(
        dataframe=selected_df,
        summary=summary,
        spatial_partition_summary=spatial_read_result.summary,
        reference_partition_summary=reference_read_result.summary,
    )


def _build_summary(
    *,
    reference_contract: CatalogContract,
    footprint: Footprint,
    spatial_parent_row_count: int,
    spatial_selected_row_count: int,
    reference_parent_row_count: int,
    selected_reference_row_count: int,
) -> dict[str, Any]:
    return {
        "reference_catalog": reference_contract.name,
        "footprint": footprint.name,
        "footprint_kind": footprint.kind,
        "effective_area_deg2": float(footprint.effective_area_deg2),
        "area_status": footprint.area_status,
        "spatial_parent_row_count": int(spatial_parent_row_count),
        "spatial_selected_row_count": int(spatial_selected_row_count),
        "reference_parent_row_count": int(reference_parent_row_count),
        "selected_reference_row_count": int(selected_reference_row_count),
        "surface_density_per_deg2": selected_reference_row_count / footprint.effective_area_deg2,
    }


def _unique_columns(columns: Iterable[str | None]) -> list[str]:
    return [column for column in dict.fromkeys(columns) if column is not None]


def _reject_repo_local_output_root(output_root: Path, *, repo_root: Path) -> None:
    resolved_output = output_root.resolve(strict=False)
    resolved_repo = repo_root.resolve(strict=False)
    if resolved_output == resolved_repo or resolved_repo in resolved_output.parents:
        raise ValueError("reference footprint output_root must be outside the repository")
