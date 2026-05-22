# ELG Selection Criteria

Last updated: 2026-05-22

## Purpose

This document describes the ELG selection intent without assuming a specific
photometric survey or catalog schema. Dataset-specific implementations translate
these rules into the available columns for one catalog.

## Selection Intent

An ELG target selection should identify galaxies likely to yield secure
emission-line redshifts in the wavelength range useful for the survey. The
DESI Main Survey ELG selection is the first reference model for this project.

The selection has four conceptual stages:

1. Define a clean photometric parent sample.
2. Require useful multi-band coverage in the selection bands.
3. Apply a magnitude or aperture-flux cut that approximates spectroscopic
   line-detection feasibility.
4. Apply color cuts that favor blue, star-forming galaxies in the desired
   redshift range.

## General Data Requirements

A dataset-specific ELG implementation should document:

- The total-flux measurement used for the broad-band colors.
- The Milky Way extinction correction used for those total fluxes.
- The aperture or fiber-like flux measurement used for the line-detection proxy.
- The bands required for a full-color parent sample.
- The image-quality and bright-object masks used to define clean photometry.
- The star-galaxy policy, if any.
- The exact output columns needed for bookkeeping and QA.

## DESI Main ELG Reference Logic

The DESI Main Survey ELG selection uses Legacy Surveys `g`, `r`, and `z`
photometry. In abstract form, after cleaning and full-color requirements:

- Require the total `g` magnitude to be fainter than a bright limit.
- Require the `g` fiber magnitude to be brighter than a faint limit.
- Require a lower bound on `r - z`.
- Require an upper bound on `g - r` as a function of `r - z` to remove stars
  and low-redshift galaxies.
- Split the remaining sample into a main ELG region and a lower-priority
  extension using another upper or bounded `g - r` line as a function of
  `r - z`.

The data-agnostic variables are:

- `g_total_mag`
- `r_total_mag`
- `z_total_mag`
- `g_aperture_mag`
- `g_minus_r = g_total_mag - r_total_mag`
- `r_minus_z = r_total_mag - z_total_mag`

The DESI-inspired photometric cuts are:

- `g_total_mag > 20`
- `g_aperture_mag < 24.1`
- `r_minus_z > 0.15`
- `g_minus_r < 0.5 * r_minus_z + 0.1`
- Main region: `g_minus_r < -1.2 * r_minus_z + 1.3`
- Lower-priority extension:
  `g_minus_r > -1.2 * r_minus_z + 1.3` and
  `g_minus_r < -1.2 * r_minus_z + 1.6`

## Translation Rule

Each dataset-specific implementation must preserve the intent of the selection
and explicitly record every approximation. If a required measurement is missing,
the implementation must either:

- Use a documented proxy.
- Omit that stage and mark the recipe as incomplete.
- Stop with a clear missing-column error.

No dataset-specific implementation should be labeled science-approved until its
proxy choices are validated against reference redshifts and target-density
requirements.
