import pandas as pd

from must_ts.catalogs.registry import CatalogContract
from must_ts.selection.reference import (
    select_reference_catalog_in_footprint,
    write_reference_footprint_selection,
)


def test_reference_selection_uses_spatial_source(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    spatial_partition = tmp_path / "spatial.csv"
    pd.DataFrame(
        {
            "object_id": [1, 2, 3],
            "ra": [150.0, 150.5, 170.0],
            "dec": [2.0, 2.1, 2.0],
            "tract": [9813, 9813, 9813],
            "patch": [0, 0, 0],
        }
    ).to_csv(spatial_partition, index=False)
    spatial_manifest = tmp_path / "spatial_manifest.csv"
    pd.DataFrame({"tract_id": [9813], "partition_path": [str(spatial_partition)]}).to_csv(
        spatial_manifest, index=False
    )

    reference_partition = tmp_path / "reference.parquet"
    pd.DataFrame(
        {
            "object_id": [1, 3],
            "z_best": [0.8, 1.2],
            "z_best_source": ["a", "b"],
        }
    ).to_parquet(reference_partition, index=False)
    reference_manifest = tmp_path / "reference_manifest.csv"
    pd.DataFrame({"tract_id": [9813], "partition_path": [str(reference_partition)]}).to_csv(
        reference_manifest, index=False
    )

    catalog_yaml = tmp_path / "catalog.yaml"
    catalog_yaml.write_text(
        f"""
name: ref
kind: reference_catalog
format: parquet_manifest
manifest_path: {reference_manifest}
path_column: partition_path
object_id_column: object_id
ra_column:
dec_column:
tract_id_column: tract_id
default_columns: [object_id, z_best, z_best_source]
footprints:
  cosmos_v0:
    kind: radec_box_assumed_area
    ra_min: 149.0
    ra_max: 151.06
    dec_min: 1.39
    dec_max: 3.07
    effective_area_deg2: 2.0
    area_status: assumed
spatial_source:
  name: spatial
  format: csv_manifest
  manifest_path: {spatial_manifest}
  path_column: partition_path
  object_id_column: object_id
  ra_column: ra
  dec_column: dec
  tract_id_column: tract_id
  default_columns: [object_id, ra, dec, tract, patch]
"""
    )
    contract = CatalogContract.from_yaml(catalog_yaml, repo_root=repo_root)

    selection = select_reference_catalog_in_footprint(
        reference_contract=contract,
        footprint=contract.footprints["cosmos_v0"],
        tract_ids=[9813],
    )

    assert selection.dataframe["object_id"].tolist() == [1]
    assert selection.summary["spatial_parent_row_count"] == 3
    assert selection.summary["spatial_selected_row_count"] == 2
    assert selection.summary["reference_parent_row_count"] == 2
    assert selection.summary["selected_reference_row_count"] == 1
    assert selection.summary["surface_density_per_deg2"] == 0.5

    output_root = tmp_path / "external"
    run_root = write_reference_footprint_selection(
        selection=selection,
        output_root=output_root,
        run_name="ref_cosmos",
        repo_root=repo_root,
    )

    assert (run_root / "selected_reference.parquet").exists()
    assert (run_root / "summary.json").exists()
