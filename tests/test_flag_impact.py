import pandas as pd

from must_ts.catalogs.registry import CatalogContract
from must_ts.qa.flag_impact import FlagImpactConfig, evaluate_reference_flag_impact


def test_evaluate_reference_flag_impact(tmp_path):
    phot_partition = tmp_path / "phot.parquet"
    pd.DataFrame(
        {
            "object_id": [1, 2, 3],
            "ra": [150.0, 150.1, 170.0],
            "dec": [2.0, 2.1, 2.0],
            "flag_a": ["False", "True", "False"],
            "flag_b": ["False", "False", "True"],
        }
    ).to_parquet(phot_partition, index=False)
    phot_manifest = tmp_path / "phot_manifest.csv"
    pd.DataFrame({"tract_id": [9813], "partition_path": [str(phot_partition)]}).to_csv(
        phot_manifest,
        index=False,
    )
    phot_yaml = tmp_path / "phot.yaml"
    phot_yaml.write_text(
        f"""
name: phot
kind: photometric_catalog
format: parquet_manifest
manifest_path: {phot_manifest}
path_column: partition_path
object_id_column: object_id
ra_column: ra
dec_column: dec
tract_id_column: tract_id
default_columns: [object_id, ra, dec]
footprints:
  cosmos_v0:
    kind: radec_box_assumed_area
    ra_min: 149.0
    ra_max: 151.06
    dec_min: 1.39
    dec_max: 3.07
    effective_area_deg2: 2.0
"""
    )
    reference_path = tmp_path / "reference.parquet"
    pd.DataFrame({"object_id": [1, 2]}).to_parquet(reference_path, index=False)
    flag_yaml = tmp_path / "flags.yaml"
    flag_yaml.write_text(
        """
name: flags
flag_groups:
  - name: group
    columns: [flag_a, flag_b]
"""
    )
    contract = CatalogContract.from_yaml(phot_yaml, repo_root=tmp_path / "repo")
    flag_config = FlagImpactConfig.from_yaml(flag_yaml)

    result = evaluate_reference_flag_impact(
        photometric_contract=contract,
        reference_selection_path=reference_path,
        flag_config=flag_config,
        footprint=contract.footprints["cosmos_v0"],
        tract_ids=[9813],
    )

    assert result.summary["joined_row_count"] == 2
    assert result.summary["any_candidate_flagged_count"] == 1
    assert result.per_flag.set_index("flag_column").loc["flag_a", "flagged_count"] == 1
    assert result.per_flag.set_index("flag_column").loc["flag_b", "flagged_count"] == 0
    assert result.per_group.set_index("flag_group").loc["group", "flagged_count"] == 1
