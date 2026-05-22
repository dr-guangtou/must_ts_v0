# ELG DESI LOP HSC S23B Reference Flag Impact

Last updated: 2026-05-22

## Inputs

- Photometric catalog: `phot_cat/s23b_i_cmod_25.2/catalog.yaml`
- Reference selection:
  `/Volumes/galaxy/must/target_selection/reference_footprints/s23b_specz_anchor_cosmos_v0/selected_reference.parquet`
- Flag groups:
  `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/candidate_flag_groups.yaml`
- Footprint: `cosmos_v0`
- Tracts: `9812`, `9813`, `9814`

## Command

```bash
uv run must-evaluate-reference-flag-impact \
  phot_cat/s23b_i_cmod_25.2/catalog.yaml \
  cosmos_v0 \
  /Volumes/galaxy/must/target_selection/reference_footprints/s23b_specz_anchor_cosmos_v0/selected_reference.parquet \
  recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/candidate_flag_groups.yaml \
  --tract-ids 9812 9813 9814 \
  --run-name elg_desi_lop_hsc_s23b_cosmos_reference_flags_v0 \
  --output-root /Volumes/galaxy/must/target_selection
```

## Output

Output root:

```text
/Volumes/galaxy/must/target_selection/qa/reference_flag_impact/elg_desi_lop_hsc_s23b_cosmos_reference_flags_v0
```

## Measured Summary

- Reference rows inside `cosmos_v0`: `161,944`
- Rows joined to current HSC photometric catalog: `154,646`
- Reference rows missing from current HSC photometric catalog: `7,298`
- Rows flagged by at least one candidate flag: `9,386`
- Fraction flagged by at least one candidate flag: `0.060693454728864636`

## Group Impact

| flag_group | flagged_count | total_count | flagged_fraction |
|---|---:|---:|---:|
| `pixel_edge_offimage` | 0 | 154,646 | 0.0 |
| `pixel_center_artifacts` | 0 | 154,646 | 0.0 |
| `pixel_bad` | 0 | 154,646 | 0.0 |
| `brightstar_masks` | 9,386 | 154,646 | 0.060693454728864636 |

## Largest Individual Flags

| flag_column | flagged_count | total_count | flagged_fraction |
|---|---:|---:|---:|
| `z_mask_brightstar_ghost` | 3,726 | 154,646 | 0.024093736663088602 |
| `z_mask_brightstar_halo` | 3,433 | 154,646 | 0.02219908694696274 |
| `z_mask_brightstar_blooming` | 2,799 | 154,646 | 0.018099401213093128 |
| `r_mask_brightstar_ghost` | 1,902 | 154,646 | 0.012299057201608836 |
| `r_mask_brightstar_halo` | 1,729 | 154,646 | 0.011180373239527695 |
| `r_mask_brightstar_blooming` | 1,613 | 154,646 | 0.010430273010617799 |
| `g_mask_brightstar_blooming` | 781 | 154,646 | 0.005050243782574395 |
| `g_mask_brightstar_halo` | 671 | 154,646 | 0.004338941841366735 |
| `g_mask_brightstar_ghost` | 215 | 154,646 | 0.0013902719759967927 |

## Notes

- HSC flag columns were read as string values such as `"False"` and `"True"`.
  The QA code now parses string booleans explicitly.
- The current pixel-flag candidates have zero measured impact on the joined
  COSMOS reference sample.
- Bright-star masks are the only candidate flags with measured impact in this
  first pass.
