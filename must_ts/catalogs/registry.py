"""Catalog contract loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from must_ts.catalogs.footprints import Footprint


@dataclass(frozen=True)
class SpatialSourceContract:
    """Coordinate-bearing external catalog used for footprint selection."""

    name: str
    format: str
    manifest_path: Path
    path_column: str
    object_id_column: str
    ra_column: str
    dec_column: str
    default_columns: tuple[str, ...]
    tract_id_column: str = "tract"

    @classmethod
    def from_mapping(
        cls,
        data: dict[str, Any],
        *,
        repo_root: Path | None = None,
    ) -> "SpatialSourceContract":
        manifest_path = Path(data["manifest_path"]).expanduser()
        if repo_root is not None:
            _reject_repo_local_data_path(manifest_path, repo_root=repo_root)
        if not manifest_path.exists():
            raise FileNotFoundError(f"spatial manifest_path does not exist: {manifest_path}")
        return cls(
            name=str(data["name"]),
            format=str(data["format"]),
            manifest_path=manifest_path,
            path_column=str(data["path_column"]),
            object_id_column=str(data["object_id_column"]),
            ra_column=str(data["ra_column"]),
            dec_column=str(data["dec_column"]),
            default_columns=tuple(data.get("default_columns", [])),
            tract_id_column=str(data.get("tract_id_column", "tract")),
        )


@dataclass(frozen=True)
class CatalogContract:
    """Tracked contract for an external catalog product."""

    name: str
    kind: str
    format: str
    manifest_path: Path
    path_column: str
    object_id_column: str
    ra_column: str | None
    dec_column: str | None
    default_columns: tuple[str, ...]
    footprints: dict[str, Footprint]
    spatial_source: SpatialSourceContract | None = None
    tract_id_column: str = "tract"

    @classmethod
    def from_yaml(cls, path: Path, *, repo_root: Path | None = None) -> "CatalogContract":
        data = _load_yaml(path)
        manifest_path = Path(data["manifest_path"]).expanduser()
        if repo_root is not None:
            _reject_repo_local_data_path(manifest_path, repo_root=repo_root)
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest_path does not exist: {manifest_path}")

        footprints = {
            name: Footprint.from_mapping(name, mapping)
            for name, mapping in data.get("footprints", {}).items()
        }
        spatial_source_data = data.get("spatial_source")
        spatial_source = (
            SpatialSourceContract.from_mapping(spatial_source_data, repo_root=repo_root)
            if spatial_source_data is not None
            else None
        )
        return cls(
            name=str(data["name"]),
            kind=str(data["kind"]),
            format=str(data["format"]),
            manifest_path=manifest_path,
            path_column=str(data["path_column"]),
            object_id_column=str(data["object_id_column"]),
            ra_column=data.get("ra_column"),
            dec_column=data.get("dec_column"),
            default_columns=tuple(data.get("default_columns", [])),
            footprints=footprints,
            spatial_source=spatial_source,
            tract_id_column=str(data.get("tract_id_column", "tract")),
        )


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    return data


def _reject_repo_local_data_path(path: Path, *, repo_root: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_repo = repo_root.resolve(strict=False)
    if resolved_path == resolved_repo or resolved_repo in resolved_path.parents:
        raise ValueError(
            "catalog data paths must be outside the repository; "
            f"got {resolved_path} under {resolved_repo}"
        )
