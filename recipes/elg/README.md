# ELG Recipes

`v0.1_cosmos_smoke.yaml` is a technical smoke recipe for exercising the
pipeline on the COSMOS footprint. It is not a science-approved ELG selection.

Each named selection family has its own subfolder. A family folder contains a
data-agnostic criteria document plus one or more dataset-specific
implementations.

`elg_desi_lop/` tracks the DESI Main Survey ELG LOP-style selection. Its HSC
S23B implementation uses HSC CModel `grz` photometry and
`g_seeing80_aper_6pix_flux` as the temporary fiber-like proxy. It is not
science-approved.

The DESI ELG Main Survey selection uses Legacy Surveys `g`, `r`, and `z`
photometry, including a `g`-band fiber magnitude cut. The current HSC S23B
catalog has useful `grz` CModel photometry, but it does not provide a direct
Legacy-style `fiberflux_g` or `maskbits` equivalent. See
`docs/references/desi_elg_selection_criteria.md` before promoting any ELG
recipe beyond smoke-test status.
