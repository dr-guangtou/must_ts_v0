from pathlib import Path

import pandas as pd
import pytest

from must_ts.catalogs.footprints import Footprint
from must_ts.catalogs.readers import read_catalog_partitions
from must_ts.catalogs.registry import CatalogContract


def test_catalog_contract_rejects_repo_local_manifest(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest_path = repo_root / "manifest.csv"
    manifest_path.write_text("partition_path\n")
    catalog_path = tmp_path / "catalog.yaml"
    catalog_path.write_text(
        "\n".join(
            [
                "name: bad",
                "kind: photometric_catalog",
                "format: parquet_manifest",
                f"manifest_path: {manifest_path}",
                "path_column: partition_path",
                "object_id_column: object_id",
                "ra_column: ra",
                "dec_column: dec",
            ]
        )
    )

    with pytest.raises(ValueError, match="outside the repository"):
        CatalogContract.from_yaml(catalog_path, repo_root=repo_root)


def test_read_catalog_partitions_filters_footprint(tmp_path):
    partition_path = tmp_path / "part.parquet"
    pd.DataFrame(
        {
            "object_id": [1, 2],
            "ra": [150.0, 170.0],
            "dec": [2.0, 2.0],
            "tract": [9813, 9813],
        }
    ).to_parquet(partition_path, index=False)
    manifest_path = tmp_path / "manifest.csv"
    pd.DataFrame({"tract_id": [9813], "partition_path": [str(partition_path)]}).to_csv(
        manifest_path, index=False
    )
    catalog_path = tmp_path / "catalog.yaml"
    catalog_path.write_text(
        "\n".join(
            [
                "name: test",
                "kind: photometric_catalog",
                "format: parquet_manifest",
                f"manifest_path: {manifest_path}",
                "path_column: partition_path",
                "object_id_column: object_id",
                "ra_column: ra",
                "dec_column: dec",
                "tract_id_column: tract_id",
                "default_columns: [object_id, ra, dec, tract]",
            ]
        )
    )
    contract = CatalogContract.from_yaml(catalog_path, repo_root=Path("/not/repo"))
    footprint = Footprint(
        name="cosmos",
        kind="radec_box_assumed_area",
        ra_min=149.0,
        ra_max=151.06,
        dec_min=1.39,
        dec_max=3.07,
        effective_area_deg2=2.0,
    )

    df = read_catalog_partitions(contract, footprint=footprint)

    assert df["object_id"].tolist() == [1]
