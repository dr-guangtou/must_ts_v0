# Architecture

Last updated: 2026-05-22

`must_ts_v0` is a bookkeeping and QA pipeline. The repository stores code,
contracts, recipes, run configs, and documentation only. Catalogs and generated
run products live outside Git under `/Volumes/galaxy/must/target_selection/`.

## Data Flow

1. A catalog contract points to an external manifest.
   Reference catalogs may also point to a coordinate-bearing spatial source.
2. A recipe contract defines required columns, derived columns, and cuts.
   Recipe folders should keep a data-agnostic criteria document beside
   dataset-specific implementations.
3. A run config combines a photometric catalog, optional reference catalog,
   recipe, footprint, and output root.
4. The runner reads only requested columns, applies the footprint, evaluates
   the recipe, writes selected targets, and creates QA tables and figures.
5. Evaluation runs join reference truth by `object_id` after selection.
6. Reference-footprint checks select spatial-source rows first, then join the
   selected coordinates to the reference truth table by `object_id`.
7. Reference-evaluation runs assemble reference truth plus photometry first,
   apply the recipe to that assembled table, and report selected surface
   density within the footprint.

## Current v0 Defaults

- External output root: `/Volumes/galaxy/must/target_selection`
- First photometric catalog: `s23b_i_cmod_25.2`
- First reference catalog: `s23b_specz_anchor`
- First footprint: `cosmos_v0`, with assumed effective area `2.0 deg^2`
- First target class: ELG technical smoke recipe
