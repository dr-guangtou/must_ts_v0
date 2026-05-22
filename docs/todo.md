# Todo

Last updated: 2026-05-22

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
