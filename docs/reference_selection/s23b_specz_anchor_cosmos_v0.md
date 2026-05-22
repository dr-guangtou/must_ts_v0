# Reference Footprint Selection: `s23b_specz_anchor` in `cosmos_v0`

Last updated: 2026-05-22

## Purpose

This note records the first reference-catalog footprint selection practice run.
The goal is to select reference objects inside the small COSMOS box before
applying ELG-specific cuts.

## Contract

- Reference catalog: `ref_cat/s23b_specz_anchor/catalog.yaml`
- Redshift lookup manifest:
  `/Volumes/galaxy/hsc/photoz/specz_merge/z_best_lookup/2026-04-11_zbest_lookup_refresh_v1/manifest/z_best_lookup_partitions_manifest.csv`
- Spatial source manifest:
  `/Volumes/galaxy/hsc/photoz/specz_merge/hsc_anchor_index/manifest/hsc_anchor_partitions_manifest.csv`
- Footprint: `cosmos_v0`
- Footprint kind: `radec_box_assumed_area`
- RA range: `[149.0, 151.06] deg`
- Dec range: `[1.39, 3.07] deg`
- Effective area: `2.0 deg^2`
- Area status: assumed
- Requested tracts for the practice run: `9812`, `9813`, `9814`

## Measured Counts

The count below was measured from the local external data on 2026-05-22.

- Spatial source rows read from requested tracts: `1,252,023`
- Spatial source rows inside `cosmos_v0`: `596,391`
- Reference lookup rows read from requested tracts: `195,291`
- Reference rows inside `cosmos_v0`: `161,944`
- Finite `z_best` rows inside `cosmos_v0`: `161,944`
- Surface density using the assumed `2.0 deg^2` area: `80,972 deg^-2`
- Output path:
  `/Volumes/galaxy/must/target_selection/reference_footprints/s23b_specz_anchor_cosmos_v0`

Top contributing `z_best_source` values:

| z_best_source | row_count |
|---|---:|
| `cosmos_web_dr1` | 66,110 |
| `desi_loa` | 54,290 |
| `hsc_specz_paus_cosmos_v_0_4_c` | 15,818 |
| `hsc_specz_3dhst_v4_1_5` | 8,140 |
| `hsc_specz_zcosmos_bright_dr3` | 4,772 |
| `hsc_specz_primus_dr1` | 4,585 |
| `hsc_specz_deimos_2018` | 2,602 |
| `legac_dr3` | 1,863 |
| `hsc_specz_c3r2_dr2` | 1,693 |
| `hsc_specz_fmos_dr2` | 989 |

## Notes

- The `z_best_lookup` partitions do not carry RA/Dec columns.
- The selection therefore reads the coordinate-bearing HSC anchor index first,
  applies the footprint there, then joins to `z_best_lookup` by `object_id`.
- Future footprint kinds should preserve the same contract: spatial filtering
  returns selected rows plus measured input and output row counts.
