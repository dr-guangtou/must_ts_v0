"""Manifest-based catalog readers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from must_ts.catalogs.footprints import Footprint
from must_ts.catalogs.registry import CatalogContract, SpatialSourceContract


@dataclass(frozen=True)
class CatalogReadResult:
    """Catalog rows plus measured partition and footprint counts."""

    dataframe: pd.DataFrame
    summary: pd.DataFrame


def load_manifest(contract: CatalogContract | SpatialSourceContract) -> pd.DataFrame:
    manifest = pd.read_csv(contract.manifest_path)
    if contract.path_column not in manifest.columns:
        raise ValueError(
            f"path column {contract.path_column!r} missing from {contract.manifest_path}"
        )
    return manifest


def read_catalog_partitions(
    contract: CatalogContract | SpatialSourceContract,
    *,
    columns: Iterable[str] | None = None,
    footprint: Footprint | None = None,
    tract_ids: Iterable[int] | None = None,
    max_partitions: int | None = None,
) -> pd.DataFrame:
    return read_catalog_partitions_with_summary(
        contract,
        columns=columns,
        footprint=footprint,
        tract_ids=tract_ids,
        max_partitions=max_partitions,
    ).dataframe


def read_catalog_partitions_with_summary(
    contract: CatalogContract | SpatialSourceContract,
    *,
    columns: Iterable[str] | None = None,
    footprint: Footprint | None = None,
    tract_ids: Iterable[int] | None = None,
    max_partitions: int | None = None,
) -> CatalogReadResult:
    manifest = load_manifest(contract)
    if tract_ids is not None and contract.tract_id_column in manifest.columns:
        tract_id_set = {int(tract_id) for tract_id in tract_ids}
        manifest = manifest[manifest[contract.tract_id_column].astype(int).isin(tract_id_set)]
    if max_partitions is not None:
        manifest = manifest.head(int(max_partitions))

    frames: list[pd.DataFrame] = []
    summary_rows = []
    read_columns = list(dict.fromkeys(columns or contract.default_columns))
    if footprint is not None:
        if contract.ra_column is None or contract.dec_column is None:
            raise ValueError(f"catalog {contract.name} has no RA/Dec columns for footprint use")
        read_columns = list(dict.fromkeys([*read_columns, contract.ra_column, contract.dec_column]))
    for _, row in manifest.iterrows():
        partition_path = _resolve_partition_path(
            row[contract.path_column], manifest_path=contract.manifest_path
        )
        if not partition_path.exists():
            raise FileNotFoundError(f"partition path does not exist: {partition_path}")
        df = _read_partition(
            partition_path,
            contract=contract,
            columns=read_columns or None,
        )
        input_row_count = len(df)
        if footprint is not None:
            df = footprint.filter_dataframe(
                df, ra_column=contract.ra_column, dec_column=contract.dec_column
            )
        output_row_count = len(df)
        summary_row = {
            "partition_path": str(partition_path),
            "input_row_count": int(input_row_count),
            "output_row_count": int(output_row_count),
        }
        if contract.tract_id_column in row.index:
            summary_row["tract_id"] = int(row[contract.tract_id_column])
        summary_rows.append(summary_row)
        frames.append(df)

    summary = pd.DataFrame(summary_rows)
    if not frames:
        return CatalogReadResult(dataframe=pd.DataFrame(columns=read_columns), summary=summary)
    return CatalogReadResult(dataframe=pd.concat(frames, ignore_index=True), summary=summary)


def _read_partition(
    partition_path: Path,
    *,
    contract: CatalogContract | SpatialSourceContract,
    columns: list[str] | None,
) -> pd.DataFrame:
    if contract.format == "parquet_manifest":
        return pd.read_parquet(partition_path, columns=columns)
    if contract.format == "csv_manifest":
        return pd.read_csv(partition_path, usecols=columns)
    raise ValueError(f"unsupported catalog format: {contract.format}")


def _resolve_partition_path(value: str, *, manifest_path: Path) -> Path:
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path
    return manifest_path.parent / path
