# MUST Target Selection v0 Specification

Last updated: 2026-05-22

## Scope

`must_ts_v0` is the v0 target-selection pipeline for the MUST spectroscopic survey. The repository should emphasize clear data contracts, reproducible bookkeeping, documented target recipes, statistical summaries, and QA figures.

The repository is not expected to develop sophisticated new algorithms at this stage. Selection rules can be simple, explicit, and versioned.

## Current Input Dataset

The current development dataset is named `s23b_i_cmod_25.2` inside this repository. It points to the assembled HSC S23B Wide local catalog at:

```text
/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all
```

The external HSC run names use underscores (`i_cmod_25_2`); the repo-facing dataset label uses a decimal magnitude spelling (`s23b_i_cmod_25.2`) for readability.

The dataset is documented in `docs/datasets/s23b_i_cmod_25.2.md`. Treat that document as the current input-data contract, not as a permanent commitment to HSC S23B. Future development may replace this dataset with a newer HSC pull or a different photometric catalog.

## Design Boundaries

- Input datasets should be described through small registry-like documents before selection code depends on them.
- Selection outputs should record the input dataset label, selection recipe version, row counts, paths, and QA sidecar paths.
- Target classes should be independent recipe modules where possible. Early planned classes include LBG, BGS, LRG, ELG, QSO, and stellar selections.
- QA outputs should include both selection-side summaries and parent-sample context.
- Large catalogs and generated science products should live outside the Git repository.
- This repo must not store catalog data or large generated outputs. It stores code, contracts, recipes, run configs, and documentation only.
- On this machine, generated MUST target-selection products should be written under `/Volumes/galaxy/must/target_selection/`.
- `/Volumes/galaxy/hsc/` is treated as an upstream HSC data area, not a MUST target-selection output area.

## Current v0 Workflow

- Catalog contracts live under `phot_cat/` and `ref_cat/`.
- Reference catalog contracts may declare a coordinate-bearing `spatial_source`
  when the truth table itself does not carry RA/Dec.
- YAML recipes live under `recipes/<target_class>/`.
- Run configs live under `run_configs/evaluation/` and `run_configs/production/`.
- Evaluation runs apply the recipe to the photometric catalog first, then join reference truth by `object_id`.
- Reference-evaluation runs assemble the reference catalog first, join
  photometric columns by `object_id`, and then apply the recipe. Use this mode
  to validate a recipe on objects with reliable redshifts.
- Reference-evaluation QA figures should compare selected targets against the
  assembled reference-plus-photometry parent sample. Current required views are
  spatial distribution, redshift distribution, color-color distribution, and
  magnitude-color distribution. Axes should use robust finite-data limits so a
  few extreme outliers do not hide the main sample.
- Production runs apply the recipe to the photometric catalog and skip the reference-truth join.
- The current COSMOS footprint contract is `RA=[149.0, 151.06]`, `Dec=[1.39, 3.07]`, with assumed effective area `2.0 deg^2`.
- The first ELG recipe is `recipes/elg/v0.1_cosmos_smoke.yaml`; it is a technical smoke recipe and is not science-approved.
- Selection recipes should separate data-agnostic science intent from
  dataset-specific translation. For ELGs, `recipes/elg/elg_desi_lop/selection_criteria.md`
  describes the general criteria, while
  `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/` contains HSC-specific translations.
- Footprint selection must report measured input and output row counts. The
  first implemented footprint kind is `radec_box_assumed_area`; future kinds may
  use polygon region files or HEALPix/HEALSparse masks while preserving the same
  count-reporting contract.

## External References

- HSC acquisition and curation reference repo: `/Users/shuang/Dropbox/work/project/otters/hsc_sandbox`
- Current HSC data root: `/Volumes/galaxy/hsc/s23b`
- DESI target-selection reference repo: `/Users/shuang/Dropbox/work/project/desi/desitarget`
- DESI structural notes for this project: `docs/references/desitarget_structure_notes.md`
