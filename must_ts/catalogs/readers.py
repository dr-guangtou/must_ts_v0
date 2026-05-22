"""Manifest-based catalog readers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from must_ts.catalogs.footprints import Footprint
from must_ts.catalogs.registry import CatalogContract


def load_manifest(contract: CatalogContract) -> pd.DataFrame:
    manifest = pd.read_csv(contract.manifest_path)
    if contract.path_column not in manifest.columns:
        raise ValueError(
            f"path column {contract.path_column!r} missing from {contract.manifest_path}"
        )
    return manifest


def read_catalog_partitions(
    contract: CatalogContract,
    *,
    columns: Iterable[str] | None = None,
    footprint: Footprint | None = None,
    tract_ids: Iterable[int] | None = None,
    max_partitions: int | None = None,
) -> pd.DataFrame:
    manifest = load_manifest(contract)
    if tract_ids is not None and contract.tract_id_column in manifest.columns:
        tract_id_set = {int(tract_id) for tract_id in tract_ids}
        manifest = manifest[manifest[contract.tract_id_column].astype(int).isin(tract_id_set)]
    if max_partitions is not None:
        manifest = manifest.head(int(max_partitions))

    frames: list[pd.DataFrame] = []
    read_columns = list(dict.fromkeys(columns or contract.default_columns))
    for _, row in manifest.iterrows():
        partition_path = _resolve_partition_path(
            row[contract.path_column], manifest_path=contract.manifest_path
        )
        if not partition_path.exists():
            raise FileNotFoundError(f"partition path does not exist: {partition_path}")
        df = pd.read_parquet(partition_path, columns=read_columns or None)
        if footprint is not None:
            if contract.ra_column is None or contract.dec_column is None:
                raise ValueError(f"catalog {contract.name} has no RA/Dec columns for footprint use")
            df = footprint.filter_dataframe(
                df, ra_column=contract.ra_column, dec_column=contract.dec_column
            )
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=read_columns)
    return pd.concat(frames, ignore_index=True)


def _resolve_partition_path(value: str, *, manifest_path: Path) -> Path:
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path
    return manifest_path.parent / path
