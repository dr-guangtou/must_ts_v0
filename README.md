# MUST Target Selection v0

`must_ts_v0` is the first bookkeeping and QA pipeline for MUST spectroscopic
survey target selection. It is built to make target-selection work reproducible:
catalog inputs are documented, selection recipes are versioned, runs write clear
counts and QA products, and large data products stay outside the Git repository.

This repository is not a data store. It contains code, catalog contracts,
selection recipes, run configs, tests, and documentation. On this machine,
catalogs and generated target-selection outputs should live under:

```text
/Volumes/galaxy/must/target_selection
```

The current development data come from local HSC S23B products prepared by
`hsc_sandbox`, but the repository is designed so the photometric catalog,
reference catalog, footprint, and recipe can all be replaced.

## Basic Rules

- Keep all code, documentation, run logs, and commit messages in English.
- Do not store catalogs or large generated products in this repository.
- Treat `docs/SPEC.md` as the source of truth for architecture and workflow.
- Describe every input dataset with a catalog contract before depending on it.
- Keep data-agnostic target-selection intent separate from dataset-specific
  translations.
- Report object counts and surface density in `N/deg^2` for every selection run.
- Validate recipes on small samples before using them for larger production
  runs.
- Mark translated or exploratory recipes as not science-approved until their
  assumptions are validated.

## Repository Map

- `phot_cat/`: photometric-catalog contracts.
- `ref_cat/`: reference-catalog contracts.
- `recipes/`: target-selection recipe families and dataset-specific recipe
  implementations.
- `run_configs/`: reusable evaluation and production run configs.
- `must_ts/`: Python package for catalog I/O, recipe evaluation, selection, and
  QA.
- `docs/`: architecture notes, dataset notes, reference notes, QA reports, and
  run reports.
- `tests/`: small tests for contracts, recipes, reference selection, and run
  outputs.

Important starting documents:

- `docs/SPEC.md`: current architecture and workflow contract.
- `docs/architecture.md`: short data-flow summary.
- `docs/datasets/s23b_i_cmod_25.2.md`: current HSC photometric dataset note.
- `docs/references/target_selection_references.md`: external target-selection
  papers and reference repositories.

## Target Selection Procedure

The normal workflow is:

1. Define or update the photometric catalog contract in `phot_cat/<dataset>/`.
2. Define or update the reference catalog contract in `ref_cat/<dataset>/` when
   validation truth is available.
3. Define the footprint and effective area used for density calculations.
4. Write the data-agnostic selection intent in a recipe-family folder.
5. Translate that intent into a dataset-specific recipe YAML file.
6. Combine catalog contracts, footprint, recipe, and output root in a run config.
7. Run the selection.
8. Inspect counts, surface density, cutflow tables, and QA figures.
9. Record what was validated, what is approximate, and what remains open.

There are three run styles:

- Reference footprint selection: select reference-catalog objects inside a
  footprint and measure the reference surface density.
- Reference evaluation: assemble reference objects first, join photometry by
  `object_id`, then apply the recipe. Use this to validate a recipe on objects
  with known redshifts.
- Production selection: apply the recipe to the photometric catalog and write
  selected targets for downstream use.

## ELG Demo

The current demo is an HSC S23B translation of the DESI ELG LOP-style selection
inside the COSMOS footprint. It is useful for exercising the workflow, but it is
not a science-approved MUST ELG selection.

Key files:

- Recipe intent:
  `recipes/elg/elg_desi_lop/selection_criteria.md`
- HSC translation:
  `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/translation.md`
- HSC recipe YAML:
  `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/v0.2_hsc_seeing80.yaml`
- Evaluation run config:
  `run_configs/evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2.yaml`
- Run report:
  `docs/evaluation/elg_desi_lop_hsc_s23b_cosmos_reference_v0.2.md`

The demo uses:

- Photometric catalog: `phot_cat/s23b_i_cmod_25.2`
- Reference catalog: `ref_cat/s23b_specz_anchor`
- Footprint: `cosmos_v0`
- Assumed effective area: `2.0 deg^2`
- Output root: `/Volumes/galaxy/must/target_selection`

Run the reference-footprint selection:

```bash
uv run must-select-reference-footprint \
  ref_cat/s23b_specz_anchor/catalog.yaml \
  cosmos_v0 \
  --tract-ids 9812 9813 9814
```

Run the ELG reference evaluation:

```bash
uv run must-evaluate-recipe \
  run_configs/evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2.yaml
```

The current measured demo output is:

- COSMOS reference rows: `161,944`
- Reference rows joined to HSC photometry: `154,646`
- Selected ELG proxy rows: `16,062`
- Selected surface density: `8,031 deg^-2`

Generated tables and figures are written outside the repository under:

```text
/Volumes/galaxy/must/target_selection/runs/reference_evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2
```

The most useful QA figures compare selected objects against the assembled
reference-plus-photometry parent sample:

- spatial distribution in COSMOS,
- redshift distribution,
- `r - z` versus `g - r`,
- seeing80 `g` aperture magnitude versus `g - r`.

## Development

Install and run checks with `uv`:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv lock --check
```

Use `uv run ruff format .` when documentation or code changes require
formatting.
