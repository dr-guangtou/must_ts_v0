# ELG DESI LOP HSC S23B COSMOS Reference Evaluation v0.2

Last updated: 2026-05-22

## Purpose

This run assembles the COSMOS reference catalog first, joins HSC S23B
photometry by `object_id`, then applies the HSC-adapted DESI LOP ELG recipe.
This is the validation order for reference catalogs.

## Inputs

- Run config:
  `run_configs/evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2.yaml`
- Mode: `reference_evaluation`
- Reference catalog: `ref_cat/s23b_specz_anchor`
- Photometric catalog: `phot_cat/s23b_i_cmod_25.2`
- Recipe:
  `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/v0.2_hsc_seeing80.yaml`
- Footprint: `cosmos_v0`
- Effective area: `2.0 deg^2`, assumed
- Tracts: `9812`, `9813`, `9814`

## Command

```bash
uv run must-evaluate-recipe \
  run_configs/evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2.yaml
```

## Output

```text
/Volumes/galaxy/must/target_selection/runs/reference_evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2
```

## Measured Summary

- Reference rows in COSMOS: `161,944`
- Reference rows joined to HSC photometry: `154,646`
- Reference rows missing HSC photometry: `7,298`
- Selected ELG LOP proxy rows: `16,062`
- Selected target surface density: `8,031 deg^-2`
- Finite selected `z_best` rows: `16,062`
- Selected `z_best` range: `0.0011198556925058` to `6.5352`

## QA Figures

The run writes selected-only figures plus reference-parent comparison figures
under:

```text
/Volumes/galaxy/must/target_selection/runs/reference_evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2/figures
```

- `reference_spatial_overlay.png`: COSMOS parent reference-plus-photometry
  objects as a 2-D sky histogram, with selected ELG proxy targets overplotted.
- `reference_redshift_overlay.png`: parent `z_best` histogram and selected
  target `z_best` outline.
- `reference_color_color_overlay.png`: parent `r - z` versus `g - r`
  2-D histogram, with selected targets highlighted.
- `reference_magnitude_color_overlay.png`: parent HSC seeing80 g-aperture
  magnitude versus `g - r` 2-D histogram, with selected targets highlighted.

The comparison figures use robust finite-data percentile limits before plotting
so a small number of extreme values does not set the visible axis range.

## Cutflow

| cut_name | kept_rows | removed_rows |
|---|---:|---:|
| `input` | 154,646 | 0 |
| `full_color_observed` | 154,646 | 0 |
| `positive_total_fluxes` | 154,580 | 66 |
| `positive_total_flux_errors` | 154,580 | 0 |
| `finite_hsc_proxy_magnitudes` | 154,476 | 104 |
| `seeing80_aperture_flux_clean` | 154,476 | 0 |
| `hsc_pixel_flags_clean` | 154,476 | 0 |
| `hsc_brightstar_masks_clean` | 145,111 | 9,365 |
| `desi_reference_g_bright_limit` | 69,334 | 75,777 |
| `hsc_seeing80_g_aperture_limit` | 69,024 | 310 |
| `desi_reference_r_minus_z_lower_bound` | 59,492 | 9,532 |
| `desi_reference_star_low_z_rejection` | 28,308 | 31,184 |
| `desi_reference_lop_region` | 16,062 | 12,246 |

## Notes

- This is not a production ELG selection.
- The high surface density is measured on the redshift-reference subset, not on
  the full photometric parent catalog.
- The selected redshift range confirms that the HSC proxy recipe still needs
  validation and likely adjustment.
