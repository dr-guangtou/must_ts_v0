# Todo

Last updated: 2026-05-22

## Current Task: README Documentation Refresh

- [x] Create a documentation branch before editing.
- [x] Move README reference-list material into `docs/`.
- [x] Rewrite `README.md` around project goals, repository rules, target-selection procedure, and the ELG demo.
- [x] Update nearby documentation that still described only the older smoke recipe.
- [x] Run verification checks and record a review.

## Review

- Replaced the scratch README with a project overview, basic rules, repository
  map, target-selection procedure, and ELG demo commands.
- Moved HSC, DESI, MUST white paper, and target-class reference links to
  `docs/references/target_selection_references.md`.
- Updated `docs/architecture.md` to identify the current worked demo as the
  HSC S23B DESI ELG LOP-style translation rather than only the original smoke
  recipe.
- Verification passed: `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run pytest`, `uv lock --check`, and
  `git diff --check`.

## Current Task: Reference-Evaluation QA Figures

- [x] Add parent-sample comparison QA figures for reference-evaluation runs.
- [x] Use robust axis limits so extreme outliers do not dominate the plots.
- [x] Run the COSMOS ELG DESI LOP HSC proxy reference evaluation and inspect the new figures.
- [x] Run verification checks and record a review.

## Review

- Added reference-parent comparison QA figures for spatial distribution,
  redshift distribution, color-color distribution, and magnitude-color
  distribution.
- The 2-D comparison figures show the assembled reference-plus-photometry
  parent sample as a logarithmically scaled histogram and selected objects as
  overplotted points.
- Axis ranges use robust finite-data percentile limits to avoid a few outliers
  dominating the view.
- Re-ran the COSMOS ELG DESI LOP HSC proxy reference evaluation and inspected
  the spatial, redshift, color-color, and magnitude-color figures.
- The measured selected target count remains `16,062`, giving `8,031 deg^-2`
  over the assumed `2.0 deg^2` COSMOS area.
- Verification passed: `uv run ruff format .`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run pytest`, `uv lock --check`, and
  `git diff --check`.
- Confirmed no catalog-like data files are stored in the repo outside the local
  `.venv`.

## Current Task: Reference-Assembled ELG Evaluation

- [x] Confirm the evaluation order should assemble reference plus photometry before applying selection.
- [x] Add `reference_evaluation` run mode.
- [x] Run the COSMOS ELG DESI LOP HSC proxy reference evaluation.
- [x] Report selected count and surface density.
- [x] Run verification checks and record a review.

## Review

- Added `reference_evaluation` mode to assemble the reference catalog first, join HSC photometry by `object_id`, then apply the recipe.
- Updated the COSMOS HSC proxy ELG run config to use `reference_evaluation`.
- Restored reference truth columns after recipe selection so validation outputs keep `z_best`.
- Ran the COSMOS ELG DESI LOP HSC proxy reference evaluation under `/Volumes/galaxy/must/target_selection/runs/reference_evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2`.
- The assembled reference-plus-photometry parent has `154,646` rows from `161,944` COSMOS reference rows.
- The recipe selected `16,062` rows, giving `8,031 deg^-2` using the assumed `2.0 deg^2` area.
- All selected rows have finite `z_best`.
- Verification passed: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`, `uv lock --check`, and `git diff --check`.

## Current Task: ELG DESI LOP Organization and Flag Impact

- [x] Reorganize ELG recipes around named selection families.
- [x] Move the DESI LOP criteria and HSC translation under `recipes/elg/elg_desi_lop/`.
- [x] Switch the HSC fiber-like proxy from `seeing65` to `seeing80`.
- [x] Add candidate HSC flag groups for the DESI LOP HSC translation.
- [x] Add a QA command for measuring candidate flag impact on reference-selected objects.
- [x] Run the flag-impact QA on the COSMOS reference selection.
- [x] Run verification checks and record a review.

## Review

- Reorganized the DESI LOP recipe family under `recipes/elg/elg_desi_lop/`.
- Renamed the HSC translated recipe to `v0.2_hsc_seeing80.yaml`.
- Updated the HSC translation to use `g_seeing80_aper_6pix_flux` as the temporary fiber-like proxy.
- Added candidate flag groups in `candidate_flag_groups.yaml`.
- Added `must-evaluate-reference-flag-impact` and measured candidate flag impact on COSMOS reference-selected objects.
- The joined reference-photometry sample contains `154,646` rows; `7,298` reference rows did not join to the current HSC photometric catalog.
- Candidate pixel flags remove `0` joined reference rows; bright-star masks flag `9,386` rows, or `0.060693454728864636`.
- Fixed string-boolean parsing for HSC flag QA and recipe expressions.
- Verification passed: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`, `uv lock --check`, and `git diff --check`.

## Current Task: ELG Recipe Translation Contract

- [x] Inspect HSC S23B columns relevant to DESI ELG translation.
- [x] Confirm spec-z anchor limitations for ELG recipe inputs.
- [x] Add a data-agnostic ELG criteria document.
- [x] Add an HSC S23B translated ELG implementation contract.
- [x] Update architecture/spec notes for recipe translation layers.
- [x] Run verification checks and record a review.

## Review

- Added `recipes/elg/elg_desi_lop/selection_criteria.md` as the data-agnostic ELG criteria contract.
- Added the HSC S23B translation note under `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/translation.md`.
- Added `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/v0.2_hsc_seeing80.yaml` as the first HSC-adapted DESI ELG proxy recipe.
- The proxy recipe uses HSC CModel `grz` magnitudes, `a_{g,r,z}` extinction corrections, input-count columns, flux errors, `g_seeing80_aper_6pix_flux`, and an initial HSC pixel/bright-star flag mask.
- Added an evaluation run config for the HSC proxy recipe in COSMOS.
- Confirmed the spec-z anchor lookup and anchor index do not carry ELG photometry; ELG validation against the reference sample must join reference IDs to the HSC photometric catalog.
- Verification passed: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`, `uv lock --check`, and `git diff --check`.

## Current Task: Reference Footprint Selection and ELG Contract

- [x] Create a feature branch before editing files.
- [x] Review lesson notes and current catalog contracts.
- [x] Verify whether the current reference catalog has RA/Dec columns.
- [x] Measure COSMOS reference counts using the HSC anchor index plus `z_best_lookup`.
- [x] Add a flexible spatial-selection contract for reference catalogs.
- [x] Add a reference-footprint selection command and tests.
- [x] Document the DESI ELG selection criteria and HSC data gaps.
- [x] Run verification checks and record a review.

## Review

- Added `spatial_source` support to reference catalog contracts.
- Added CSV-manifest partition reading and partition-level input/output row-count summaries.
- Added `must-select-reference-footprint` for selecting reference objects inside a footprint.
- Ran the real COSMOS reference-footprint selection for `s23b_specz_anchor` with tracts `9812`, `9813`, and `9814`.
- Measured `161,944` selected reference rows inside `cosmos_v0`, giving `80,972 deg^-2` using the assumed `2.0 deg^2` area.
- Wrote the selected reference product outside Git at `/Volumes/galaxy/must/target_selection/reference_footprints/s23b_specz_anchor_cosmos_v0`.
- Documented the DESI ELG Main Survey cuts and HSC S23B data gaps in `docs/references/desi_elg_selection_criteria.md`.
- Verification passed: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`, `uv lock --check`, and `git diff --check`.

## Current Task: Document Current HSC Dataset

- [x] Create a feature branch before editing files.
- [x] Read the project README and HSC sandbox context.
- [x] Inspect `/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all` manifests and tract products.
- [x] Measure current row counts, schema size, product counts, and field coverage from local metadata.
- [x] Review the local DESI `desitarget` repository structure for later pipeline discussion.
- [x] Write the current dataset document for `s23b_i_cmod_25.2`.

## Review

- Current branch: `docs/current-hsc-dataset`.
- Main dataset document: `docs/datasets/s23b_i_cmod_25.2.md`.
- DESI reference note: `docs/references/desitarget_structure_notes.md`.
- No source code was added in this pass.

## Current Task: Implement v0 Architecture Scaffold

- [x] Add the durable no-data-in-repo rule.
- [x] Add catalog, recipe, and run-config contracts.
- [x] Add package code for manifest-based I/O, safe YAML recipes, evaluation, production, and QA outputs.
- [x] Add a COSMOS ELG technical smoke recipe and run configs.
- [x] Add tests for catalog validation, recipe evaluation, and end-to-end tiny evaluation runs.

## Review

- Added the `must_ts` Python package and `uv` project setup.
- Added catalog contract folders for `phot_cat/s23b_i_cmod_25.2` and `ref_cat/s23b_specz_anchor`.
- Added the ELG `v0.1_cosmos_smoke` recipe plus evaluation and production run configs.
- Confirmed the real catalog manifests resolve outside the repository:
  `/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all/global_tract_manifest.csv`
  and
  `/Volumes/galaxy/hsc/photoz/specz_merge/z_best_lookup/2026-04-11_zbest_lookup_refresh_v1/manifest/z_best_lookup_partitions_manifest.csv`.
- Created the external generated-output root:
  `/Volumes/galaxy/must/target_selection`.
- Verification passed: `uv run ruff check .`, `uv run ruff format --check .`, and `uv run pytest`.
