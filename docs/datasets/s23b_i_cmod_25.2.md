# HSC Dataset: `s23b_i_cmod_25.2`

Last updated: 2026-05-22

## Purpose

`s23b_i_cmod_25.2` is the current photometric parent dataset for early `must_ts_v0` development. It is a local HSC S23B Wide catalog assembled by the `hsc_sandbox` repo. Use it to prototype target-selection recipes, output bookkeeping, statistics, and QA figures.

This label is a development contract, not a permanent survey-data choice. If the photometric input is updated or replaced, create a new dataset document and point `docs/SPEC.md` at the new label.

## Provenance

- Source helper repo: `/Users/shuang/Dropbox/work/project/otters/hsc_sandbox`
- Source database and layer: HSC internal `dr4`, `s23b_wide`
- Local data root: `/Volumes/galaxy/hsc/s23b`
- Assembled analysis root: `/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all`
- Global manifest CSV: `/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all/global_tract_manifest.csv`
- Global manifest JSON: `/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all/global_tract_manifest.json`
- Completed tract registry: `/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all/completed_tracts.txt`

The external run names use `i_cmod_25_2`, while this repo label uses `s23b_i_cmod_25.2`.

## Acquisition Contract

The catalog was fetched tract by tract from `s23b_wide`. The generated SQL used these core parent cuts:

- `f1.isprimary`
- `TRACTSEARCH(f1.object_id, <tract_id>)`
- patch is present in `s23b_wide.mosaic` with all five broad bands
- `f1.i_cmodel_mag <= 25.2`
- `g/r/i/z/y_inputcount_value >= 3`
- no `g/r/i/z/y_pixelflags_edge`
- no central saturated, interpolated, or cosmic-ray flags in `g/r/i/z/y`

The table strategy is one base `forced` query joined to selected payload tables. The production table set is:

```text
forced2 forced3 forced4 forced5 forced6 meas meas2 photoz_mizuki masks
```

`masks` is fetched as a direct tract-level table and joined locally. Other payloads use pairwise `forced + table` queries.

## Local Layout

The assembled root contains one symlink per finalized tract:

```text
/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all/<tract_id> -> /Volumes/galaxy/hsc/s23b/<run_name>/<tract_id>
```

Each tract directory contains:

- `sql/`: generated SQL and rename maps
- `csv/`: downloaded HSC CSV files, usually compressed as `*.csv.gz` after validation
- `parquet/`: merged tract parquet product
- `qa/`: tract-level QA tables, JSON summaries, and figures
- `subset/`: post-download initial subset parquet and compact target-list CSV
- `logs/`: tract journals and validation reports
- `manifest_tract.json`: tract-level inventory

Each run root contains `manifest_sample.json`, `pipeline_report.json`, `postprocess_report.json`, `initial_subset_report.json`, and usually `logs/run_journal.jsonl`.

## Measured Inventory

Measured from local manifests and Parquet metadata on 2026-05-22:

| Quantity | Value |
| --- | ---: |
| Assembled tracts | `849` |
| Symlinked tract directories | `849` |
| Source sample roots in global manifest | `74` |
| Missing merged/subset/summary products | `0` |
| Merged parent rows | `232,289,768` |
| Initial subset rows | `185,673,933` |
| Empty parent tracts | `110` |
| Non-empty parent tracts | `739` |
| Empty initial-subset tracts | `116` |
| Non-empty initial-subset tracts | `733` |
| Merged parquet columns per tract | `661` |
| Summary row-count mismatches found | `0` |
| Merged parquet total size | `640,520,051,929` bytes |
| Initial subset parquet total size | `520,733,367,892` bytes |

The `hsc_sandbox` verification summary dated 2026-03-31 reports `849` assembled tracts, `739` verified non-empty tracts, `110` empty-selection tracts, and `0` integrity issues.

## Field and Run Coverage

Measured from `global_tract_manifest.csv`:

| Field or source group | Tracts | Parent rows | Initial subset rows |
| --- | ---: | ---: | ---: |
| `W-AEGIS` | `4` | `351,763` | `281,850` |
| `W-autumn` | `360` | `91,925,946` | `73,977,399` |
| `W-hectomap` | `78` | `15,625,216` | `12,382,235` |
| `W-spring` | `404` | `123,134,820` | `97,915,237` |
| Two-tract reference run | `2` | `837,277` | `751,153` |
| Smoke tract `9812` | `1` | `414,746` | `366,059` |

The smoke tract is present in the assembled root and should be treated as part of the current local dataset unless a later cleanup removes it from the manifest.

## Schema Content

Every measured merged tract parquet has `661` columns. The first columns are stable identifiers and coordinates:

```text
object_id, ra, dec, tract, patch
```

Important column families include:

- Galactic extinction context: `a_g`, `a_r`, `a_i`, `a_z`, `a_y`
- merge-measurement flags for broad and narrow bands
- broad-band `g/r/i/z/y` CModel fluxes, errors, flags, fracdev values, and shape columns
- broad-band extendedness and input-count columns
- many broad-band pixel-level QA flags
- undeblended aperture-style photometry renamed from HSC convolved flux families
- deblend and blendedness columns
- Mizuki photo-z columns: `photoz_mode`, `photoz_median`, `photoz_best`, confidence, risk, and error intervals
- Mizuki physical context: `stellar_mass`, `sfr`, and uncertainty intervals
- bright-star mask columns

The compact target-list CSV in each tract subset currently keeps only:

```text
object_id, ra, dec, tract
```

## Initial Subset

The initial subset is a post-download filter, not part of the HSC SQL query. It keeps rows satisfying:

- valid `cmodel` photometry in all five broad bands using finite `cmodel_flux` and `cmodel_flag = false`
- `g_extendedness_value > 0.5`
- `r_extendedness_value > 0.5`
- `i_extendedness_value > 0.5`
- `i_inputcount_value >= 5`

Central problematic-pixel filters were already applied during SQL acquisition. Bright-object masks are retained as columns but are not applied in this initial subset.

For early MUST target-selection development, the initial subset is the more practical parent table for galaxy selections. The full merged parent parquet is still useful for debugging, stellar work, alternative cuts, and QA.

## QA Products

Each tract has QA sidecars under `qa/`, typically including:

- `tract_quality_summary.json`
- `tract_quality_measurements.csv`
- `tract_quality_extendedness.csv`
- `tract_quality_inputcount.csv`
- `tract_quality_flags.csv`
- flag-fraction and invalid-fraction figures
- bright-object-mask impact figure when applicable

Each subset has `subset/initial_subset_summary.json`, which records input and selected row counts plus the subset criteria.

## Practical Use in `must_ts_v0`

Recommended first read path:

1. Read `/Volumes/galaxy/hsc/s23b/i_cmod_25_2_all/global_tract_manifest.csv`.
2. Use `subset_parquet_path` for first-pass galaxy target recipes.
3. Use `merged_parquet_path` when a recipe needs columns outside the initial subset or needs to inspect rejected rows.
4. Always write outputs with the dataset label `s23b_i_cmod_25.2`, the source manifest path, and the selection recipe version.

Do not assume that future datasets will be HSC, tract-based, or have the same 661-column schema. Code should route through a dataset manifest layer where possible.

## Known Caveats

- The dataset is a selected local HSC S23B Wide extract, not the full HSC database.
- It is limited by the `i_cmodel_mag <= 25.2` acquisition cut and the SQL-level quality cuts.
- It covers the five-band-complete Wide tract inventory assembled by `hsc_sandbox`; it is not a Deep or UltraDeep catalog.
- The assembled root includes one smoke tract (`9812`) alongside production and reference runs.
- Object IDs are HSC S23B/DR4 identifiers. They should not be assumed compatible with older HSC releases or non-HSC catalogs.
- The compact target-list CSV is intentionally minimal and is not sufficient for most selection recipes.
