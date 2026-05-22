# Target Selection References

Last updated: 2026-05-22

This document collects external target-selection papers, reference codebases,
and local upstream-data context. The README should stay focused on how to use
this repository.

## Local Data Context

- HSC acquisition and curation repo:
  `/Users/shuang/Dropbox/work/project/otters/hsc_sandbox`
- Current local HSC data root:
  `/Volumes/galaxy/hsc/s23b`
- Current development dataset note:
  `docs/datasets/s23b_i_cmod_25.2.md`

## Reference Codebases

- DESI target selection:
  <https://github.com/desihub/desitarget>
- DESI target-selection structure notes for this repo:
  `docs/references/desitarget_structure_notes.md`
- DESI BGS selection scripts:
  <https://github.com/qmxp55/bgstargets>

## Target Classes

### Lyman Break Galaxies

- MUST white paper:
  <https://arxiv.org/html/2411.07970v4>
- Current note: the HSC development data are most immediately useful for
  `g`- and `r`-dropout exploration.

### Bright Galaxy Samples

- DESI BGS target selection:
  <https://arxiv.org/abs/2208.08512>

### Luminous Red Galaxies

- DESI LRG target selection:
  <https://arxiv.org/abs/2208.08515>

### Emission Line Galaxies

- DESI ELG target selection:
  <https://arxiv.org/abs/2208.08513>
- Local ELG criteria note:
  `docs/references/desi_elg_selection_criteria.md`
- Current ELG recipe family:
  `recipes/elg/elg_desi_lop/`

### Quasars

- DESI QSO target selection:
  <https://arxiv.org/abs/2208.08511>
