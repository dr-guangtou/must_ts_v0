# Reference Catalog: `s23b_specz_anchor`

This folder stores the tracked contract for the current curated HSC-attached
`z_best` reference lookup from `hsc_sandbox`. It does not store reference data.

The lookup is keyed by `object_id` and stores redshift fields only. It does not
carry RA/Dec columns, so footprint-aware reference selections use the
coordinate-bearing HSC anchor index declared as `spatial_source` in
`catalog.yaml`, then join the spatially selected anchor rows to this lookup.

Evaluation runs apply recipes to a photometric catalog first, then join this
truth lookup by `object_id`.
