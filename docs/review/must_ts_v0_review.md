---
title: "MUST Target Selection v0 — Development Review"
subtitle: "Pipeline architecture, current status, and the COSMOS ELG demo"
author: "MUST target-selection development"
date: "2026-05-26"
---

# Executive Summary

`must_ts_v0` is the first bookkeeping and quality-assurance pipeline for
target selection in the MUST spectroscopic survey. Target selection is the
step that decides which objects in a deep photometric catalog should be
observed spectroscopically. The pipeline is intentionally narrow in scope:
it does not yet propose new selection algorithms, and it does not store any
large data products in version control. Its purpose at this stage is to
make every selection run reproducible, inspectable, and easy to compare
against a reference truth sample.

This document is written for a funding-review audience that may not have
followed the day-to-day development of the project. It introduces the
target-selection problem, summarizes the design principles behind the
current pipeline, walks through the codebase as it stands today, and
explains the worked Emission-Line Galaxy (ELG) demonstration in detail.
A companion script, `scripts/run_elg_demo.py`, reproduces the entire demo
end-to-end and narrates each step in plain language.

The headline numbers from the current demo, measured on the local HSC
S23B Wide catalog inside the COSMOS field with an assumed effective area
of 2.0 deg²:

| Quantity                                             | Value          |
| ---------------------------------------------------- | -------------: |
| Reference-truth rows in COSMOS footprint             |       161,944  |
| Reference rows joined to HSC photometry              |       154,646  |
| Reference rows missing in HSC photometry             |         7,298  |
| Selected ELG-proxy targets                           |        16,062  |
| Selected surface density                             | 8,031 deg⁻²    |

The demo recipe is deliberately labeled `science_approved: false`. It is a
faithful translation of the DESI Main Survey ELG LOP-style selection into
HSC S23B columns, but it relies on HSC-native proxies for two DESI
ingredients (the Legacy Surveys fiber flux and the Legacy Surveys mask
bits). The proxies are documented and are intended to be validated, not
silently accepted, before they can be used to drive a real MUST target
list.

# Background

## MUST and target selection

MUST is a planned wide-field, fiber-fed spectroscopic survey. Like any
fiber-fed survey, MUST needs an input list of celestial objects — *targets*
— for each pointing of the instrument. Target selection is the step that
turns a deep photometric catalog into a prioritized list of targets per
target class (luminous red galaxies, emission-line galaxies, quasars,
high-redshift galaxies, bright galaxy samples, stellar samples, and so on).
A good selection has three properties simultaneously:

1. **Cosmologically useful**: it picks objects whose redshifts will be
   useful for the survey's science goals, in the right redshift ranges and
   in the right number density.
2. **Spectroscopically tractable**: it picks objects whose lines or
   features are bright enough to be measured by the instrument in a
   reasonable exposure time.
3. **Reproducible**: it is defined precisely enough that a later person —
   or a later version of the pipeline — can rebuild the same target list
   from the same inputs.

The first two properties are largely science questions and depend on
detailed knowledge of the instrument, the data, and the cosmological
analysis plan. The third property is an engineering question, and it is
the one this repository takes responsibility for first. The premise is
that the science work has to happen on top of a reliable bookkeeping
layer, so we built the bookkeeping layer first.

## What "v0" means

The label `v0` is deliberate. The pipeline is allowed to be simple,
explicit, and even slightly verbose, as long as everything it does is
documented and rerunnable. Recipes can be one-line color cuts; the
machinery just needs to record what was cut, on which catalog, with which
recipe version, and what the resulting density was. New target classes,
new datasets, and new recipes will be added on top of this v0 scaffold.

# Repository Design

## Guiding rules

The repository follows a small set of durable rules that are encoded in
`docs/SPEC.md`, `AGENTS.md`, and `docs/lessons.md`. The most important
ones for an outside reviewer:

- **No catalogs in Git.** The repository contains only code, contracts,
  recipes, run configs, documentation, and small tests. Catalogs and
  generated run outputs live entirely on a separate volume
  (`/Volumes/galaxy/must/target_selection/` on the development machine).
  This keeps the repository small and forces every dependency on an
  external dataset to go through an explicit contract.
- **Data-agnostic intent, dataset-specific translation.** Each target
  class has a written description of *what* the selection is trying to do
  in survey-independent terms, separate from *how* that selection is
  expressed in any one photometric catalog. Translating intent into a
  specific dataset is treated as a documented step, not as an inline
  assumption.
- **Surface density is always reported.** Every selection run records the
  selected row count, the assumed effective area, and the resulting
  surface density in objects per square degree, alongside the cutflow
  table that shows how many rows each cut kept.
- **Recipes start as "not science approved".** A recipe is marked
  `science_approved: false` until its proxies and numerical thresholds
  have been validated against a reference sample. Nothing in the
  pipeline prevents an unapproved recipe from running, but the label is
  carried into the run summary so that downstream readers know whether
  the result is a proxy or a science product.

## Repository map

The high-level layout is:

```text
must_ts_v0/
├── must_ts/                   # Python package (catalogs, recipes, selection, QA, CLIs)
├── phot_cat/                  # photometric catalog contracts
├── ref_cat/                   # reference catalog contracts
├── recipes/                   # versioned selection recipes
├── run_configs/               # evaluation + production run configs
├── scripts/                   # demo and review helpers (this addition)
├── tests/                     # contract, recipe, and engine tests
└── docs/
    ├── SPEC.md                # architecture source of truth
    ├── architecture.md        # short data-flow summary
    ├── datasets/              # per-dataset notes
    ├── references/            # external selection references
    ├── reference_selection/   # measured reference selections
    ├── evaluation/            # per-run evaluation reports
    ├── qa/                    # QA studies
    ├── review/                # this review document
    ├── lessons.md             # cumulative lessons learned
    └── todo.md                # active and completed tasks
```

## Pipeline data flow

The pipeline is a four-stage data flow that maps cleanly onto four kinds
of contracts:

1. **Catalog contract** (YAML in `phot_cat/<dataset>/` or
   `ref_cat/<dataset>/`). Points at an external manifest, declares the
   identifier and coordinate columns, lists the column families needed by
   default, and names one or more footprints.
2. **Recipe** (YAML in `recipes/<target_class>/...`). Declares which
   columns it requires, any derived columns it computes, the cuts to
   apply, and which columns to keep in the output.
3. **Footprint** (declared inside a catalog contract). Defines the spatial
   region used for density calculations and an effective-area value with
   a status flag (`measured`, `assumed`, etc.).
4. **Run config** (YAML in `run_configs/`). Combines a photometric
   catalog, an optional reference catalog, a recipe, a footprint, an
   output root, and a list of tract IDs into one runnable unit.

The Python package `must_ts/` reads these contracts, loads only the
columns it needs from the external parquet manifests, applies the
selection, and writes per-run outputs to the external output volume.
Generated outputs always include:

- `selected_targets.parquet` and `selected_targets.csv`
- `tables/cutflow.csv` — rows kept and removed at each cut
- `tables/density_summary.csv` — selected count, effective area, density
- `tables/redshift_summary.csv` — counts of attached redshifts
- `summary.json` and `resolved_inputs.yaml` — inputs and headline numbers
- `figures/` — PNG QA figures
- `logs/run.log` — JSON log of the run

The three supported run modes are:

- **`reference_footprint`** — select reference-truth objects inside a
  footprint and measure their surface density. Used to characterize the
  reference sample itself.
- **`reference_evaluation`** — assemble the reference truth, join HSC
  photometry by `object_id`, then apply the recipe to that joined table.
  Used to validate a recipe on objects whose redshifts we already know.
- **`production`** — apply the recipe to the full photometric catalog
  and skip the reference-truth join. Used to write target lists for
  downstream use.

The demo described below is a `reference_evaluation` run, which is the
mode that exercises the largest fraction of the pipeline.

# The COSMOS ELG Demo

## Why ELGs and why COSMOS

Emission-line galaxies are a natural first target class for a
demonstration because the DESI Main Survey already provides a
well-documented selection, and because the line-detection logic gives the
pipeline a non-trivial cut family to exercise. The demo is restricted to
the COSMOS field for three reasons:

1. COSMOS is fully contained in the HSC S23B Wide footprint we have
   locally.
2. The HSC spec-z anchor (`s23b_specz_anchor`) has dense COSMOS coverage,
   so the reference-evaluation join produces a useful parent sample.
3. Restricting to three HSC tracts (`9812`, `9813`, `9814`) keeps the
   wall-clock time manageable while still producing meaningful counts.

The COSMOS footprint contract is a simple RA/Dec box
(`149.0° ≤ RA ≤ 151.06°`, `1.39° ≤ Dec ≤ 3.07°`) with an *assumed*
effective area of 2.0 deg². The status flag is `assumed`, not `measured`,
to make clear that no mask-aware area calculation has been done yet for
this demo.

## Demo inputs

| Input              | Identifier                                                          |
| ------------------ | ------------------------------------------------------------------- |
| Photometric catalog | `phot_cat/s23b_i_cmod_25.2`                                        |
| Reference catalog   | `ref_cat/s23b_specz_anchor`                                        |
| Spatial source      | `s23b_hsc_anchor_index` (declared inside the reference contract)   |
| Footprint           | `cosmos_v0` (radec_box_assumed_area, 2.0 deg²)                     |
| Recipe              | `elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/v0.2_hsc_seeing80`           |
| Run mode            | `reference_evaluation`                                             |
| Tract filter        | `9812`, `9813`, `9814`                                             |
| Output root         | `/Volumes/galaxy/must/target_selection`                             |

The photometric catalog is the assembled HSC S23B Wide product with
`i_cmodel_mag ≤ 25.2`, built by the separate `hsc_sandbox` repository. It
totals 849 tracts and roughly 232 million parent rows; the demo only
touches a tiny fraction of those rows because the footprint is small.

The reference catalog `s23b_specz_anchor` is the HSC `z_best` lookup
table. It carries no RA/Dec column of its own; coordinates come from an
auxiliary HSC anchor index declared in the reference contract as
`spatial_source`. The pipeline reads the anchor index to find which HSC
objects fall inside COSMOS, then joins those objects back to the truth
table by `object_id`.

## The recipe

The recipe is a 1:1 translation of the DESI Main Survey ELG LOP-style
selection into HSC columns. The translation is documented in detail in
`recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/translation.md`. The
intent layer is documented in
`recipes/elg/elg_desi_lop/selection_criteria.md`.

Conceptually the recipe has four stages:

1. **Clean photometric parent.** Require full-color observations in `g`,
   `r`, `z` (non-zero input counts), positive CModel fluxes and flux
   errors, finite proxy magnitudes, a clean seeing80 aperture flux, clean
   HSC pixel flags, and clean HSC bright-star masks.
2. **Multi-band magnitudes.** Convert HSC CModel fluxes to magnitudes,
   subtract HSC `a_{g,r,z}` extinction corrections, and compute
   `g - r` and `r - z` colors.
3. **Magnitude and aperture limits.** Require `g_total_mag > 20.0` (the
   DESI bright limit) and `g_aperture_mag < 24.1` (the DESI fiber-flux
   line-detection proxy, mapped onto the HSC seeing80 6-pixel aperture).
4. **Color box.** Apply the DESI Main ELG lower bound on `r - z`, the
   star/low-redshift rejection line, and the LOP-region upper bound on
   `g - r`.

The HSC-specific proxy choices (the seeing80 aperture magnitude in place
of the Legacy Surveys fiber flux; HSC pixel + bright-star masks in place
of Legacy Surveys `maskbits`) are why the recipe is not yet
science-approved.

## Demo results

The demo ran on 2026-05-22 and writes outputs to:

```text
/Volumes/galaxy/must/target_selection/runs/reference_evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2/
```

The cutflow shows where the recipe loses rows:

| Cut                                       | Rows kept | Rows removed |
| ----------------------------------------- | --------: | -----------: |
| input                                     |   154,646 |            0 |
| full_color_observed                       |   154,646 |            0 |
| positive_total_fluxes                     |   154,580 |           66 |
| positive_total_flux_errors                |   154,580 |            0 |
| finite_hsc_proxy_magnitudes               |   154,476 |          104 |
| seeing80_aperture_flux_clean              |   154,476 |            0 |
| hsc_pixel_flags_clean                     |   154,476 |            0 |
| hsc_brightstar_masks_clean                |   145,111 |        9,365 |
| desi_reference_g_bright_limit             |    69,334 |       75,777 |
| hsc_seeing80_g_aperture_limit             |    69,024 |          310 |
| desi_reference_r_minus_z_lower_bound      |    59,492 |        9,532 |
| desi_reference_star_low_z_rejection       |    28,308 |       31,184 |
| desi_reference_lop_region                 |    16,062 |       12,246 |
| **final selection**                       | **16,062**|              |

Two cuts do most of the work: the DESI `g`-bright limit removes the bulk
of the foreground galaxies, and the star/low-redshift color line removes
about half of the remaining sample. The LOP color box gives the final
factor of about two. The aperture-flux and pixel-flag cuts remove very
few rows because the parent photometric catalog already had similar
quality cuts applied during acquisition. The bright-star masks remove
roughly six percent of the joined reference-photometry sample, which is
in line with previous QA on HSC bright-object masks.

The headline result is **16,062 selected ELG-proxy targets in
2.0 deg²**, i.e. **8,031 deg⁻²**. This is a sensible order of magnitude
for a DESI ELG LOP-style cut applied to a deeper HSC catalog, but it is
not directly comparable to the DESI value because the proxies and depth
differ.

## QA figures

The reference-evaluation QA figures live in
`runs/reference_evaluation/.../figures/`. They are deliberately compact
and use robust percentile axis limits so that a few outliers do not hide
the bulk of the sample. The figures most useful for the review are:

- `reference_spatial_overlay.png` — COSMOS RA/Dec map showing the joined
  reference-plus-photometry parent sample as a log-scaled 2-D histogram
  and the selected ELG candidates overplotted in red.
- `reference_redshift_overlay.png` — `z_best` histogram for the reference
  parent and the selected sample, useful for checking whether the
  recipe is preferentially picking the redshift range we want for ELGs.
- `reference_color_color_overlay.png` — `r - z` vs `g - r` color-color
  plane with the LOP color box visible by construction in the selected
  sample.
- `reference_magnitude_color_overlay.png` — HSC seeing80 `g` aperture
  magnitude vs `g - r` color, useful for checking how the
  fiber-flux proxy behaves at the faint end.

The same `figures/` directory also contains single-distribution figures
(`sky_distribution.png`, `redshift_distribution.png`) which use only the
selected sample. For the review, the overlay figures are the more useful
comparison because they show the selection against its parent.

# Reproducing the Demo

## One-shot demo script

The demo is reproducible end-to-end via a single script,
`scripts/run_elg_demo.py`, which is the companion to this document. In
its default mode it narrates each step in plain language before
performing it. To run the script:

```bash
# Default verbose mode (recommended for review)
uv run python scripts/run_elg_demo.py

# Quiet mode (only essential output, useful for CI smoke tests)
uv run python scripts/run_elg_demo.py --quiet

# Skip the standalone reference-footprint selection
uv run python scripts/run_elg_demo.py --skip-reference-footprint
```

The script performs five steps:

1. **Inspect the photometric catalog contract** — confirms that the
   external manifest is reachable and reports its row count.
2. **Inspect the reference catalog contract** — confirms that the truth
   manifest is reachable and reports the auxiliary spatial source used
   to attach coordinates.
3. **Reference-footprint selection** — runs the `select_reference_*`
   pipeline to count truth objects inside COSMOS and write the
   selection to disk outside the repository.
4. **Reference-evaluation run** — invokes the same code path used by
   `must-evaluate-recipe`, assembling the joined parent sample, applying
   the recipe, restoring reference-truth columns, and writing every QA
   product.
5. **Inspect demo outputs** — prints the summary JSON, the cutflow, and
   the list of QA figures produced.

Each step prints a multi-paragraph explanation before it runs when
verbose mode is on. The non-verbose mode prints only the essential lines
(input identities, elapsed times, and row counts) so it can be used as a
quick smoke test.

The script does not add new pipeline behavior. It only chains together
existing entry points (`must_ts.catalogs.registry.CatalogContract`,
`must_ts.catalogs.readers.load_manifest`,
`must_ts.selection.reference.select_reference_catalog_in_footprint`,
`must_ts.selection.engine.run_configured_selection`). The intent is to
make the existing pipeline observable rather than to introduce a new
demo-only code path.

## Equivalent low-level CLIs

The same demo can also be reproduced using the installed entry points
declared in `pyproject.toml`:

```bash
# Step 3 only
uv run must-select-reference-footprint \
  ref_cat/s23b_specz_anchor/catalog.yaml \
  cosmos_v0 \
  --tract-ids 9812 9813 9814

# Step 4 only
uv run must-evaluate-recipe \
  run_configs/evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2.yaml
```

The script wraps both with consistent narration and reads back the
generated summary so that reviewers can see the result without opening
JSON or CSV files by hand.

# Limitations and Roadmap

## What this version does *not* do

This is `v0`, and the scope is intentionally small. In particular:

- **No new selection science.** The current ELG recipe is a translation
  proxy. It is not a tuned MUST ELG selection and it has not been
  validated against MUST-specific science goals.
- **No mask-aware area.** The effective area is currently an assumed
  constant per footprint. Bright-star and pixel masks affect the
  effective area but are not yet folded back into the density
  calculation.
- **No multi-class orchestration.** Only ELGs have a worked recipe
  family at the moment. LRGs, BGS, QSO, LBG, and stellar selections are
  expected but not implemented.
- **Single-machine assumption.** The pipeline reads parquet partitions
  serially with pandas/pyarrow. This is fine for COSMOS-scale demos and
  for small-scale validation, but a production run on the full HSC S23B
  Wide footprint will need parallel or distributed I/O.
- **HSC-only photometry.** Only one photometric catalog contract exists.
  The contract layer is designed so that adding a second photometric
  catalog should be a documentation-and-contract change rather than a
  rewrite, but the second catalog has not yet been added.

## Near-term plan

The natural next steps, in roughly the order they should happen:

1. **Validate the HSC ELG proxy against COSMOS reference redshifts.**
   The recipe is already exercised end-to-end; the next pass is to
   measure its redshift completeness and the contamination from
   low-redshift galaxies and stars, then adjust the color boundaries
   and the fiber-flux proxy.
2. **Add at least one more target class.** LRGs are the most natural
   second target class for HSC because the relevant photometry is
   already in the contract.
3. **Tighten effective area accounting.** Replace `area_status: assumed`
   with mask-aware effective areas for the COSMOS demo, and add a
   footprint kind that can read polygon or HEALPix mask files.
4. **Multi-recipe production runs.** Add a small orchestrator that runs
   several recipes against the same photometric catalog and writes a
   combined target list with priority labels.
5. **Move beyond a single development machine.** Wrap the parquet I/O
   layer so it can run against a chunked or distributed backend without
   changing the recipes or contracts.

# Appendix: Key Files for the Reviewer

For a reviewer who wants to inspect the actual artifacts:

- `docs/SPEC.md` — current architecture and workflow contract.
- `docs/architecture.md` — short data-flow summary.
- `docs/datasets/s23b_i_cmod_25.2.md` — current HSC dataset note.
- `phot_cat/s23b_i_cmod_25.2/catalog.yaml` — photometric contract.
- `ref_cat/s23b_specz_anchor/catalog.yaml` — reference contract.
- `recipes/elg/elg_desi_lop/selection_criteria.md` — data-agnostic ELG
  intent.
- `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/translation.md` — HSC
  translation notes.
- `recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/v0.2_hsc_seeing80.yaml`
  — the recipe used in the demo.
- `run_configs/evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2.yaml`
  — the run config used in the demo.
- `scripts/run_elg_demo.py` — the one-shot reproducible demo with
  verbose narration.
- `docs/evaluation/elg_desi_lop_hsc_s23b_cosmos_reference_v0.2.md` —
  the demo's evaluation report.
- `docs/lessons.md` — cumulative lessons learned during development.

The generated demo outputs live under
`/Volumes/galaxy/must/target_selection/runs/reference_evaluation/elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2/`
and contain the QA figures, the per-cut row counts, and the run
summary JSON discussed above.
