# Lessons

Last updated: 2026-05-22

## 2026-05-22

- This repository started without prior local lesson notes. Future mistakes, surprising data behavior, and durable rationale should be recorded here as they occur.
- The current HSC input is an assembled local catalog built by `hsc_sandbox`, not a direct live view of the HSC database. Project code should depend on a documented dataset label and manifest path, not hard-code assumptions about all future photometric inputs.
- Catalog manifests are not guaranteed to share the same metadata columns. The HSC reference manifest has `row_count`, while the current HSC photometric manifest does not, so code should require only the configured path and tract columns.
- Command examples should match the installed script names in `pyproject.toml`; this project currently uses `must-inspect-catalog`, `must-evaluate-recipe`, and `must-select-targets`.
- The current `s23b_specz_anchor` truth lookup does not carry RA/Dec columns. Reference footprint selection must use the HSC anchor index as a coordinate-bearing spatial source, then join by `object_id`.
- DESI ELG selection depends on Legacy Surveys `fiberflux_g`, `maskbits`, and `nobs`/inverse-variance columns. The current HSC S23B catalog has useful translations through seeing-aperture fluxes, pixel and bright-star flags, input-count columns, and flux errors, but HSC ELG recipes must be labeled as adapted until those mappings are validated.
- HSC boolean-like flag columns can arrive as strings such as `"False"` and `"True"`. Flag-impact code must parse string booleans explicitly instead of using a direct boolean cast.
- Reference-evaluation selected tables must restore reference truth columns after recipe selection. Recipe output columns are target-bookkeeping fields and should not be trusted to retain validation truth such as `z_best`.
- Reference QA figures should show selected targets against the assembled parent sample and should use robust finite-data axis limits. A few extreme color, magnitude, or redshift values can otherwise hide the main distribution.
