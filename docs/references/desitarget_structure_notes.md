# DESI `desitarget` Structure Notes

Last updated: 2026-05-22

Reference checkout:

```text
/Users/shuang/Dropbox/work/project/desi/desitarget
```

## What It Does

DESI `desitarget` selects targets from photometric catalogs, assigns target bits, writes target tables, and provides QA, masking, sky, random, secondary-target, and MTL-related tooling.

For `must_ts_v0`, the useful lesson is structural: separate data reading, selection rules, target-bit bookkeeping, output writing, and QA.

## Important Files and Directories

- `bin/select_targets`: command-line entry point for main target selection.
- `py/desitarget/cuts.py`: main survey selection logic; contains target-class functions such as `isLRG`, `isELG`, `isBGS`, and QSO selection helpers.
- `py/desitarget/targets.py`: target ID encoding, bit handling, priority logic, and final target-table assembly.
- `py/desitarget/io.py`: catalog reading, file discovery, data-model handling, and output helpers.
- `py/desitarget/data/targetmask.yaml`: declarative bit definitions for DESI target classes, observing conditions, and related masks.
- `py/desitarget/QA.py`: target-selection QA tools.
- `py/desitarget/brightmask.py`, `skyfibers.py`, `randoms.py`, `secondary.py`, `mtl.py`: supporting target classes and operational products.
- `py/desitarget/sv1`, `sv2`, `sv3`, `cmx`: survey-validation and commissioning variants.
- `py/desitarget/test/`: unit tests for cuts, I/O, masks, target IDs, QA, and survey variants.

## Design Ideas Worth Adapting

- Keep each target class as an explicit function that returns a boolean mask.
- Keep target identity and target-class membership as bookkeeping columns separate from selection logic.
- Define target-class bits in a data file, not scattered through selection code.
- Keep finalization logic separate from cut logic. In DESI this is where IDs, bit columns, subpriorities, and observing conditions are assembled.
- Keep command-line entry points thin: parse inputs, find files, call library functions, and write outputs.
- Include QA as a first-class product rather than an afterthought.

## Differences for MUST v0

`must_ts_v0` can be simpler than DESI `desitarget`:

- HSC input should start from a manifest of Parquet files, not Legacy Surveys sweeps.
- MUST v0 does not need full DESI-style MTL, secondary-target, sky-fiber, random-catalog, or survey-validation machinery at the beginning.
- A compact target-class registry can be enough before a full bitmask system is needed.
- Output products should focus on selected target tables, per-selection summaries, and QA figures.

## Suggested Early Shape for This Repo

```text
docs/
  datasets/
  references/
  recipes/
must_ts/
  data/
  datasets/
  recipes/
  selection/
  qa/
  io/
tests/
```

This is only a planning note. The exact package structure should be discussed after the current HSC dataset contract is accepted.
