"""End-to-end demo of the MUST target-selection v0 workflow.

This script walks through the full COSMOS ELG demo in one go. It is the
companion to ``docs/review/must_ts_v0_review.md`` and is designed for readers
who are not yet familiar with the codebase: in the default verbose mode it
narrates every step before running it.

Run with the project virtualenv:

    uv run python scripts/run_elg_demo.py
    uv run python scripts/run_elg_demo.py --quiet
    uv run python scripts/run_elg_demo.py --skip-reference-footprint

The demo only exercises code paths that already exist in the repository; the
intent is to make the existing pipeline observable, not to add new behavior.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml

from must_ts.catalogs.readers import load_manifest
from must_ts.catalogs.registry import CatalogContract, SpatialSourceContract
from must_ts.selection.engine import run_configured_selection
from must_ts.selection.reference import (
    select_reference_catalog_in_footprint,
    write_reference_footprint_selection,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUN_CONFIG = (
    REPO_ROOT / "run_configs" / "evaluation" / "elg_s23b_specz_anchor_cosmos_hsc_proxy_v0.2.yaml"
)
DEFAULT_OUTPUT_ROOT = Path("/Volumes/galaxy/must/target_selection")


@dataclass(frozen=True)
class DemoOptions:
    """Resolved demo configuration."""

    run_config_path: Path
    repo_root: Path
    output_root: Path | None
    reference_run_name: str
    skip_reference_footprint: bool
    verbose: bool


def main() -> int:
    options = parse_options()
    _print_intro(options)
    run_config = _read_run_config(options)

    _section(options, "Step 1", "Inspect the photometric catalog contract")
    _explain(
        options,
        """
        The photometric catalog is the parent sample we draw candidates from.
        It is described by a small YAML contract in ``phot_cat/``. The contract
        only points at an external manifest; the catalog itself is not in this
        repository. Inspecting it confirms that the manifest is reachable and
        tells us how many parquet partitions the pipeline will scan.
        """,
    )
    phot_contract = _resolve_phot_contract(run_config, options)
    _inspect_catalog(phot_contract, options, label="photometric catalog")

    _section(options, "Step 2", "Inspect the reference catalog contract")
    _explain(
        options,
        """
        The reference catalog provides spectroscopic redshift truth for
        validation. The current contract (``s23b_specz_anchor``) does not
        carry RA/Dec itself; coordinates come from a separate HSC anchor
        index declared as ``spatial_source``. The pipeline will join those
        coordinates back to the truth table by ``object_id``.
        """,
    )
    ref_contract = _resolve_ref_contract(run_config, options)
    _inspect_catalog(ref_contract, options, label="reference catalog")
    if ref_contract.spatial_source is not None:
        _inspect_catalog(
            ref_contract.spatial_source,
            options,
            label="reference spatial source",
        )

    if options.skip_reference_footprint:
        _explain(
            options,
            """
            Skipping the standalone reference-footprint selection because
            ``--skip-reference-footprint`` was passed. The same selection
            happens internally during the reference evaluation in Step 4.
            """,
        )
    else:
        _section(
            options,
            "Step 3",
            "Select reference objects inside the COSMOS footprint",
        )
        _explain(
            options,
            """
            Before validating a recipe, we measure how many reference-truth
            objects live inside the footprint. This is the
            ``reference_footprint`` run mode. It reads only the columns it
            needs from the spatial source, applies the RA/Dec box, then joins
            the surviving object IDs back to the truth table. The resulting
            row count divided by the assumed effective area gives the
            reference surface density we will later compare the recipe
            against.
            """,
        )
        _run_reference_footprint(ref_contract, run_config, options)

    _section(options, "Step 4", "Run the reference-evaluation end-to-end")
    _explain(
        options,
        """
        The reference-evaluation mode is the heart of the demo. It assembles
        the reference-plus-photometry parent sample first, then applies the
        recipe to that joined table. This lets us validate the recipe against
        objects whose redshifts we already know. The recipe being applied is
        the HSC S23B translation of the DESI Main ELG LOP-style selection
        (``recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/v0.2_hsc_seeing80``);
        it is intentionally labeled ``science_approved: false`` because the
        HSC proxies for DESI fiber flux and Legacy Survey masks have not yet
        been validated.
        """,
    )
    evaluation_result = _run_reference_evaluation(options)

    _section(options, "Step 5", "Inspect demo outputs")
    _summarize_outputs(evaluation_result, options)
    _print_outro(options)
    return 0


def parse_options() -> DemoOptions:
    parser = argparse.ArgumentParser(
        description=(
            "Run the MUST target-selection v0 ELG demo end-to-end with verbose narration."
        ),
    )
    parser.add_argument(
        "--run-config",
        type=Path,
        default=DEFAULT_RUN_CONFIG,
        help="Path to the reference-evaluation run config YAML (default: COSMOS ELG demo).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve contract paths (default: this checkout).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help=(
            "Override the output root used for the reference-footprint selection. "
            "Defaults to the path declared in the run config, or "
            f"{DEFAULT_OUTPUT_ROOT} if absent."
        ),
    )
    parser.add_argument(
        "--reference-run-name",
        type=str,
        default=None,
        help=(
            "Optional name for the reference-footprint output directory. "
            "Defaults to ``<reference_catalog>_<footprint>``."
        ),
    )
    parser.add_argument(
        "--skip-reference-footprint",
        action="store_true",
        help="Skip the standalone reference-footprint selection step.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Turn off verbose narration. Defaults to verbose=True.",
    )
    args = parser.parse_args()

    return DemoOptions(
        run_config_path=args.run_config.resolve(),
        repo_root=args.repo_root.resolve(),
        output_root=args.output_root.resolve() if args.output_root is not None else None,
        reference_run_name=args.reference_run_name or "",
        skip_reference_footprint=args.skip_reference_footprint,
        verbose=not args.quiet,
    )


def _print_intro(options: DemoOptions) -> None:
    if not options.verbose:
        print(f"must_ts_v0 ELG demo (run config: {options.run_config_path.name})")
        return
    print("=" * 78)
    print("MUST Target Selection v0 — ELG Demo")
    print("=" * 78)
    print(
        dedent(
            """
            MUST is a planned spectroscopic survey. Target selection is the step
            that decides which objects in a photometric catalog should be
            observed spectroscopically. This repository ("must_ts_v0") is the
            v0 bookkeeping and QA pipeline for that step: it stores catalog
            contracts, versioned recipes, and run configs, and produces small
            tables and figures we can inspect.

            This demo runs the current worked example end-to-end:

              * Photometric catalog : HSC S23B Wide ``i_cmodel < 25.2`` subset
              * Reference truth     : HSC spec-z anchor (``z_best`` lookup)
              * Footprint           : COSMOS RA/Dec box, assumed 2.0 deg^2
              * Recipe              : HSC translation of the DESI Main ELG
                                      LOP-style selection (not science-approved)

            The demo only reproduces the existing pipeline. It does not add new
            selection logic. Verbose mode (default) explains each step before
            running it; pass ``--quiet`` to suppress narration.
            """
        ).strip()
    )
    print(f"\nRepository root : {options.repo_root}")
    print(f"Run config      : {options.run_config_path}")
    print()


def _print_outro(options: DemoOptions) -> None:
    if not options.verbose:
        return
    print()
    print("-" * 78)
    print("Demo complete.")
    print(
        dedent(
            """
            To inspect the run yourself:

              * Open the figures under ``runs/reference_evaluation/<run-name>/figures``
                for the QA views compared against the parent sample.
              * Open ``summary.json`` and ``tables/cutflow.csv`` for the
                quantitative breakdown of each cut.

            The numbers reported above are the verbatim demo result. Treat
            them as a sanity check of the pipeline, not as the final MUST ELG
            target list — the recipe is still a translation proxy.
            """
        ).strip()
    )


def _section(options: DemoOptions, label: str, title: str) -> None:
    print()
    if options.verbose:
        print("-" * 78)
        print(f"{label} — {title}")
        print("-" * 78)
    else:
        print(f"[{label}] {title}")


def _explain(options: DemoOptions, message: str) -> None:
    if not options.verbose:
        return
    text = dedent(message).strip()
    if not text:
        return
    print(text)
    print()


def _read_run_config(options: DemoOptions) -> dict[str, Any]:
    with options.run_config_path.open() as handle:
        run_config = yaml.safe_load(handle) or {}
    if not isinstance(run_config, dict):
        raise ValueError(f"run config YAML must contain a mapping: {options.run_config_path}")
    return run_config


def _resolve_phot_contract(run_config: dict[str, Any], options: DemoOptions) -> CatalogContract:
    return CatalogContract.from_yaml(
        options.repo_root / "phot_cat" / run_config["photometric_catalog"] / "catalog.yaml",
        repo_root=options.repo_root,
    )


def _resolve_ref_contract(run_config: dict[str, Any], options: DemoOptions) -> CatalogContract:
    return CatalogContract.from_yaml(
        options.repo_root / "ref_cat" / run_config["reference_catalog"] / "catalog.yaml",
        repo_root=options.repo_root,
    )


def _inspect_catalog(
    contract: CatalogContract | SpatialSourceContract,
    options: DemoOptions,
    *,
    label: str,
) -> None:
    manifest = load_manifest(contract)
    kind = contract.kind if isinstance(contract, CatalogContract) else "spatial_source"
    print(f"  {label}: {contract.name}")
    print(f"    kind             : {kind}")
    print(f"    manifest_path    : {contract.manifest_path}")
    print(f"    manifest_rows    : {len(manifest)}")
    print(f"    object_id_column : {contract.object_id_column}")
    if options.verbose:
        if contract.ra_column and contract.dec_column:
            print(f"    coords           : {contract.ra_column}, {contract.dec_column}")
        else:
            print("    coords           : not carried on this table")
        spatial_source = getattr(contract, "spatial_source", None)
        if spatial_source is not None:
            print(f"    spatial_source   : {spatial_source.name} (format={spatial_source.format})")


def _run_reference_footprint(
    ref_contract: CatalogContract,
    run_config: dict[str, Any],
    options: DemoOptions,
) -> None:
    footprint_name = run_config["footprint"]
    footprint = ref_contract.footprints[footprint_name]
    tract_ids = run_config.get("tract_ids")
    output_root = options.output_root or Path(
        run_config.get("output_root", str(DEFAULT_OUTPUT_ROOT))
    )
    run_name = options.reference_run_name or f"{ref_contract.name}_{footprint_name}"

    print(f"  footprint         : {footprint_name}")
    print(
        f"    box (RA, Dec)   : ({footprint.ra_min}, {footprint.ra_max}) x "
        f"({footprint.dec_min}, {footprint.dec_max})"
    )
    print(f"    effective area  : {footprint.effective_area_deg2} deg^2 ({footprint.area_status})")
    if tract_ids:
        print(f"  tract filter      : {list(tract_ids)}")
    print(f"  output_root       : {output_root}")

    start = time.perf_counter()
    selection = select_reference_catalog_in_footprint(
        reference_contract=ref_contract,
        footprint=footprint,
        tract_ids=tract_ids,
    )
    run_root = write_reference_footprint_selection(
        selection=selection,
        output_root=output_root,
        run_name=run_name,
        repo_root=options.repo_root,
    )
    elapsed = time.perf_counter() - start
    summary = selection.summary
    print(f"  elapsed           : {elapsed:0.1f} s")
    print(f"  selected_rows     : {summary['selected_reference_row_count']}")
    print(f"  surface_density   : {summary['surface_density_per_deg2']:0.1f} deg^-2")
    print(f"  written to        : {run_root}")
    if options.verbose:
        print()
        print(
            "  Note: the reference surface density above ("
            f"{summary['surface_density_per_deg2']:0.1f} deg^-2) is the density of "
            "all reference-truth objects with HSC coordinates in COSMOS, not the "
            "ELG target density. The recipe in Step 4 selects a much smaller "
            "subset."
        )


def _run_reference_evaluation(options: DemoOptions) -> dict[str, Any]:
    start = time.perf_counter()
    result = run_configured_selection(options.run_config_path, repo_root=options.repo_root)
    elapsed = time.perf_counter() - start
    print(f"  elapsed           : {elapsed:0.1f} s")
    print(f"  run_root          : {result['run_root']}")
    print(f"  parent_row_count  : {result['parent_row_count']}")
    print(f"  selected_count    : {result['selected_row_count']}")
    return result


def _summarize_outputs(result: dict[str, Any], options: DemoOptions) -> None:
    run_root = Path(result["run_root"])
    summary_path = run_root / "summary.json"
    cutflow_path = run_root / "tables" / "cutflow.csv"
    figures_dir = run_root / "figures"

    if not summary_path.exists():
        print(f"  summary.json not found at {summary_path}")
        return

    summary = json.loads(summary_path.read_text())
    print("  Run summary (from summary.json):")
    for key in (
        "parent_row_count",
        "reference_selected_row_count",
        "reference_photometry_joined_row_count",
        "reference_photometry_missing_row_count",
        "selected_count",
        "surface_density_per_deg2",
        "effective_area_deg2",
        "area_status",
        "science_approved",
    ):
        if key in summary:
            print(f"    {key:<42}: {summary[key]}")

    if options.verbose:
        print()
        print("  Cutflow (per-cut rows kept):")
        try:
            for line in cutflow_path.read_text().splitlines():
                print(f"    {line}")
        except FileNotFoundError:
            print(f"    cutflow.csv not found at {cutflow_path}")

    print()
    print("  QA figures written under figures/:")
    if figures_dir.exists():
        for path in sorted(figures_dir.iterdir()):
            print(f"    {path.name}")
        if options.verbose:
            print()
            print(
                "  The most useful views are ``reference_spatial_overlay.png`` "
                "(COSMOS sky distribution), ``reference_redshift_overlay.png`` "
                "(redshift distribution against the truth parent), "
                "``reference_color_color_overlay.png`` (r-z vs g-r), and "
                "``reference_magnitude_color_overlay.png`` (HSC seeing80 g "
                "aperture magnitude vs g-r)."
            )
    else:
        print(f"    figures directory missing: {figures_dir}")


if __name__ == "__main__":
    raise SystemExit(main())
