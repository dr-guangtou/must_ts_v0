# DESI ELG Selection Criteria Notes

Last updated: 2026-05-22

Source: Raichoor et al., "Target Selection and Validation of DESI Emission Line
Galaxies", arXiv:2208.08513, especially Table 2 and Section 3.3.

## Main Survey Cuts

DESI Main Survey ELG targeting uses Legacy Surveys `grz` photometry. It defines
two disjoint ELG classes:

- `ELG_LOP`, the higher-density main sample.
- `ELG_VLO`, the lower-priority extension.

Both classes start from a clean imaging sample:

- Unique primary object.
- Observed in `g`, `r`, and `z`.
- Positive signal-to-noise in `g`, `r`, and `z`.
- Not close to bright-star or bright-galaxy mask regions.

Both classes use:

- `g > 20`
- `gfib < 24.1`
- `r - z > 0.15`
- `g - r < 0.5 * (r - z) + 0.1`

The split between `ELG_LOP` and `ELG_VLO` is:

- `ELG_LOP`: `g - r < -1.2 * (r - z) + 1.3`
- `ELG_VLO`: `g - r > -1.2 * (r - z) + 1.3` and
  `g - r < -1.2 * (r - z) + 1.6`

DESI computes `g`, `r`, and `z` from Legacy Surveys total flux divided by
Milky Way transmission, and computes `gfib` from Legacy Surveys `g`-band fiber
flux divided by Milky Way transmission.

## HSC S23B Availability

Available now in `s23b_i_cmod_25.2`:

- HSC `g`, `r`, `i`, `z`, `y` CModel fluxes and flux errors.
- HSC Galactic extinction columns such as `a_g`, `a_r`, and `a_z`.
- HSC `*_inputcount_value` columns that can support a full-depth, full-color
  requirement.
- HSC seeing-aperture fluxes such as `g_seeing80_aper_6pix_flux` and
  `g_seeing80_aper_6pix_flux`, which can act as temporary fiber-flux proxies.
- HSC pixel flags, CModel flags, and bright-star mask family columns.
- HSC aperture, PSF, seeing-aperture, and GAaP flux families.
- HSC `photoz_*`, stellar mass, and star-formation-rate columns.

Missing or not directly equivalent:

- A direct Legacy Surveys `fiberflux_g`; HSC seeing-aperture fluxes are only
  temporary proxies.
- Direct Legacy Surveys `nobs_g`, `nobs_r`, and `nobs_z`; HSC input-count
  columns are the current translation.
- Direct Legacy Surveys `flux_ivar_g`, `flux_ivar_r`, and `flux_ivar_z`; HSC
  flux-error columns are the current translation.
- Legacy Surveys `maskbits` with the DESI bright-star/galaxy bit meanings.
- A calibrated color transformation from HSC to Legacy Surveys `grz`.
- DESI spectroscopic [O II] flux and `DELTACHI2`, which are used for
  spectroscopic validation rather than photometric target selection.

## Practical HSC Contract Implications

- The DESI color-box structure can be represented in the MUST recipe system.
- The current HSC demo should not call itself a DESI-equivalent ELG selection
  until the fiber-flux proxy, mask, and photometric-system decisions are
  validated.
- A first HSC ELG contract can use HSC CModel `g`, `r`, and `z` colors as a
  proxy and explicitly label the recipe as HSC-adapted and not science-approved.
- The `gfib < 24.1` step is currently approximated using an HSC seeing-aperture
  flux; this proxy needs validation.
- The clean-sample step needs a decision: map DESI `maskbits` to HSC pixel and
  bright-star masks, or define an independent HSC-native cleanliness contract.
