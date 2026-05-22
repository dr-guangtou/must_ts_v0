# HSC S23B ELG Translation

Last updated: 2026-05-22

## Dataset

- Photometric catalog: `phot_cat/s23b_i_cmod_25.2`
- Reference catalog for validation: `ref_cat/s23b_specz_anchor`
- Initial footprint: `cosmos_v0`

## Translation Choices

This implementation translates the DESI Main Survey ELG logic to HSC S23B
columns. It is a proxy recipe for development and validation, not a
science-approved target selection.

| General concept | DESI reference | HSC S23B translation |
|---|---|---|
| Total `g`, `r`, `z` magnitudes | Legacy Surveys total flux corrected by `mw_transmission` | HSC CModel fluxes corrected by `a_g`, `a_r`, `a_z` |
| Milky Way extinction correction | `mw_transmission_{g,r,z}` | subtract `a_{g,r,z}` after flux-to-magnitude conversion |
| Full-color observations | `nobs_g`, `nobs_r`, `nobs_z` | `g_inputcount_value`, `r_inputcount_value`, `z_inputcount_value`; currently required to be `> 0` |
| Positive SNR | `flux * sqrt(flux_ivar) > 0` | positive CModel flux and positive CModel flux error in `g`, `r`, and `z` |
| Fiber-like `g` magnitude | `fiberflux_g` | `g_seeing80_aper_6pix_flux` corrected by `a_g` |
| Clean bright-object masks | DESI `maskbits` | initial HSC-native pixel and bright-star flags in `g`, `r`, and `z` |

## HSC Proxy Caveats

- `g_seeing80_aper_6pix_flux` is not a DESI fiber flux. It is used only as a
  temporary line-detection proxy.
- The HSC mask mapping is intentionally conservative but not yet validated.
- HSC and Legacy Surveys filters and photometric measurements are not identical.
- The recipe keeps the DESI color-box form, but the numerical boundaries may
  need adjustment after COSMOS reference-catalog validation.
- The spec-z anchor lookup lacks ELG photometry. Validation against reference
  redshifts must join reference IDs to the HSC photometric catalog.

## Current Decisions

- Use `g_seeing80_aper_6pix_flux` as the default temporary fiber-like proxy.

## Open Decisions

- Whether the mask list should include all bands or only the bands used in each
  measurement.
- Whether to define separate HSC-adapted `LOP` and `VLO` target classes or keep
  a single recipe with an output priority label.
- Whether to include star-galaxy separation in the ELG clean sample.
