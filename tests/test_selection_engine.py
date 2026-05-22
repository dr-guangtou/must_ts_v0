from pathlib import Path

import pandas as pd

from must_ts.selection.engine import run_configured_selection


def test_run_configured_evaluation_writes_outputs(tmp_path):
    repo_root = tmp_path / "repo"
    (repo_root / "phot_cat" / "phot").mkdir(parents=True)
    (repo_root / "ref_cat" / "ref").mkdir(parents=True)
    (repo_root / "recipes" / "elg").mkdir(parents=True)

    phot_partition = tmp_path / "phot.parquet"
    pd.DataFrame(
        {
            "object_id": [1, 2, 3],
            "ra": [150.0, 150.5, 170.0],
            "dec": [2.0, 2.1, 2.0],
            "tract": [9813, 9813, 9813],
            "g_cmodel_flux": [100.0, 10.0, 100.0],
            "r_cmodel_flux": [80.0, 100.0, 80.0],
            "i_cmodel_flux": [70.0, 100.0, 70.0],
            "z_cmodel_flux": [60.0, 100.0, 60.0],
            "a_g": [0.0, 0.0, 0.0],
            "a_r": [0.0, 0.0, 0.0],
            "a_i": [0.0, 0.0, 0.0],
            "a_z": [0.0, 0.0, 0.0],
        }
    ).to_parquet(phot_partition, index=False)
    phot_manifest = tmp_path / "phot_manifest.csv"
    pd.DataFrame({"tract_id": [9813], "subset_parquet_path": [str(phot_partition)]}).to_csv(
        phot_manifest, index=False
    )
    (repo_root / "phot_cat" / "phot" / "catalog.yaml").write_text(
        f"""
name: phot
kind: photometric_catalog
format: parquet_manifest
manifest_path: {phot_manifest}
path_column: subset_parquet_path
object_id_column: object_id
ra_column: ra
dec_column: dec
tract_id_column: tract_id
default_columns: [object_id, ra, dec, tract]
footprints:
  cosmos_v0:
    kind: radec_box_assumed_area
    ra_min: 149.0
    ra_max: 151.06
    dec_min: 1.39
    dec_max: 3.07
    effective_area_deg2: 2.0
    area_status: assumed
"""
    )

    ref_partition = tmp_path / "ref.parquet"
    pd.DataFrame({"object_id": [1], "z_best": [0.8]}).to_parquet(ref_partition, index=False)
    ref_manifest = tmp_path / "ref_manifest.csv"
    pd.DataFrame({"tract_id": [9813], "partition_path": [str(ref_partition)]}).to_csv(
        ref_manifest, index=False
    )
    (repo_root / "ref_cat" / "ref" / "catalog.yaml").write_text(
        f"""
name: ref
kind: reference_catalog
format: parquet_manifest
manifest_path: {ref_manifest}
path_column: partition_path
object_id_column: object_id
ra_column:
dec_column:
tract_id_column: tract_id
default_columns: [object_id, z_best]
footprints: {{}}
"""
    )
    recipe_text = """
target_class: elg
version: smoke
science_approved: false
required_columns:
  - object_id
  - ra
  - dec
  - tract
  - g_cmodel_flux
  - r_cmodel_flux
  - i_cmodel_flux
  - z_cmodel_flux
  - a_g
  - a_r
  - a_i
  - a_z
derived_columns:
  - name: g_cmodel_mag_mw
    expression: mag_from_flux(g_cmodel_flux, a_g)
  - name: r_cmodel_mag_mw
    expression: mag_from_flux(r_cmodel_flux, a_r)
  - name: g_minus_r
    expression: g_cmodel_mag_mw - r_cmodel_mag_mw
cuts:
  - name: blue
    expression: g_minus_r < 0.5
output_columns: [object_id, ra, dec, tract, g_cmodel_mag_mw, r_cmodel_mag_mw, g_minus_r]
"""
    (repo_root / "recipes" / "elg" / "smoke.yaml").write_text(recipe_text)
    run_config = tmp_path / "run.yaml"
    output_root = tmp_path / "external"
    run_config.write_text(
        f"""
name: eval
mode: evaluation
photometric_catalog: phot
reference_catalog: ref
recipe: elg/smoke
footprint: cosmos_v0
output_root: {output_root}
tract_ids: [9813]
"""
    )

    result = run_configured_selection(run_config, repo_root=repo_root)

    run_root = Path(result["run_root"])
    assert result["parent_row_count"] == 2
    assert result["selected_row_count"] == 1
    assert (run_root / "summary.json").exists()
    selected = pd.read_parquet(run_root / "selected_targets.parquet")
    assert selected["object_id"].tolist() == [1]
    assert selected["z_best"].tolist() == [0.8]


def test_run_configured_reference_evaluation_assembles_reference_first(tmp_path):
    repo_root = tmp_path / "repo"
    (repo_root / "phot_cat" / "phot").mkdir(parents=True)
    (repo_root / "ref_cat" / "ref").mkdir(parents=True)
    (repo_root / "recipes" / "elg").mkdir(parents=True)

    phot_partition = tmp_path / "phot.parquet"
    pd.DataFrame(
        {
            "object_id": [1, 2, 3],
            "ra": [150.0, 150.5, 150.6],
            "dec": [2.0, 2.1, 2.2],
            "tract": [9813, 9813, 9813],
            "g_flux": [100.0, 10.0, 100.0],
            "r_flux": [80.0, 100.0, 80.0],
            "a_g": [0.0, 0.0, 0.0],
            "a_r": [0.0, 0.0, 0.0],
        }
    ).to_parquet(phot_partition, index=False)
    phot_manifest = tmp_path / "phot_manifest.csv"
    pd.DataFrame({"tract_id": [9813], "subset_parquet_path": [str(phot_partition)]}).to_csv(
        phot_manifest, index=False
    )
    (repo_root / "phot_cat" / "phot" / "catalog.yaml").write_text(
        f"""
name: phot
kind: photometric_catalog
format: parquet_manifest
manifest_path: {phot_manifest}
path_column: subset_parquet_path
object_id_column: object_id
ra_column: ra
dec_column: dec
tract_id_column: tract_id
default_columns: [object_id, ra, dec, tract]
footprints:
  cosmos_v0:
    kind: radec_box_assumed_area
    ra_min: 149.0
    ra_max: 151.06
    dec_min: 1.39
    dec_max: 3.07
    effective_area_deg2: 2.0
    area_status: assumed
"""
    )

    spatial_partition = tmp_path / "spatial.csv"
    pd.DataFrame(
        {
            "object_id": [1, 2],
            "ra": [150.0, 150.5],
            "dec": [2.0, 2.1],
            "tract": [9813, 9813],
            "patch": [0, 0],
        }
    ).to_csv(spatial_partition, index=False)
    spatial_manifest = tmp_path / "spatial_manifest.csv"
    pd.DataFrame({"tract_id": [9813], "partition_path": [str(spatial_partition)]}).to_csv(
        spatial_manifest, index=False
    )
    ref_partition = tmp_path / "ref.parquet"
    pd.DataFrame({"object_id": [1, 2], "z_best": [0.8, 1.1]}).to_parquet(ref_partition, index=False)
    ref_manifest = tmp_path / "ref_manifest.csv"
    pd.DataFrame({"tract_id": [9813], "partition_path": [str(ref_partition)]}).to_csv(
        ref_manifest, index=False
    )
    (repo_root / "ref_cat" / "ref" / "catalog.yaml").write_text(
        f"""
name: ref
kind: reference_catalog
format: parquet_manifest
manifest_path: {ref_manifest}
path_column: partition_path
object_id_column: object_id
ra_column:
dec_column:
tract_id_column: tract_id
default_columns: [object_id, z_best]
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
    (repo_root / "recipes" / "elg" / "smoke.yaml").write_text(
        """
target_class: elg
version: smoke
science_approved: false
required_columns: [object_id, ra, dec, tract, g_flux, r_flux, a_g, a_r]
derived_columns:
  - name: g_mag
    expression: mag_from_flux(g_flux, a_g)
  - name: r_mag
    expression: mag_from_flux(r_flux, a_r)
  - name: g_minus_r
    expression: g_mag - r_mag
cuts:
  - name: blue
    expression: g_minus_r < 0.5
output_columns: [object_id, ra, dec, tract, g_mag, r_mag, g_minus_r]
"""
    )
    run_config = tmp_path / "run.yaml"
    output_root = tmp_path / "external"
    run_config.write_text(
        f"""
name: ref_eval
mode: reference_evaluation
photometric_catalog: phot
reference_catalog: ref
recipe: elg/smoke
footprint: cosmos_v0
output_root: {output_root}
tract_ids: [9813]
"""
    )

    result = run_configured_selection(run_config, repo_root=repo_root)

    run_root = Path(result["run_root"])
    assert result["parent_row_count"] == 2
    assert result["selected_row_count"] == 1
    selected = pd.read_parquet(run_root / "selected_targets.parquet")
    assert selected["object_id"].tolist() == [1]
    assert selected["z_best"].tolist() == [0.8]
    density = pd.read_csv(run_root / "tables" / "density_summary.csv")
    assert density["surface_density_per_deg2"].tolist() == [0.5]
    assert (run_root / "figures" / "reference_spatial_overlay.png").exists()
    assert (run_root / "figures" / "reference_redshift_overlay.png").exists()
