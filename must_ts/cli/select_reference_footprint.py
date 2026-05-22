"""CLI for selecting reference-catalog objects inside a footprint."""

from __future__ import annotations

import argparse
from pathlib import Path

from must_ts.catalogs.registry import CatalogContract
from must_ts.selection.reference import (
    select_reference_catalog_in_footprint,
    write_reference_footprint_selection,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select reference-catalog objects inside a configured footprint."
    )
    parser.add_argument("catalog_yaml", type=Path)
    parser.add_argument("footprint")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/Volumes/galaxy/must/target_selection"),
    )
    parser.add_argument("--run-name")
    parser.add_argument("--tract-ids", nargs="*", type=int)
    parser.add_argument("--max-partitions", type=int)
    args = parser.parse_args()

    reference_contract = CatalogContract.from_yaml(args.catalog_yaml, repo_root=args.repo_root)
    footprint = reference_contract.footprints[args.footprint]
    selection = select_reference_catalog_in_footprint(
        reference_contract=reference_contract,
        footprint=footprint,
        tract_ids=args.tract_ids,
        max_partitions=args.max_partitions,
    )
    run_name = args.run_name or f"{reference_contract.name}_{footprint.name}"
    run_root = write_reference_footprint_selection(
        selection=selection,
        output_root=args.output_root,
        run_name=run_name,
        repo_root=args.repo_root,
    )
    print(f"run_root={run_root}")
    print(f"selected_reference_row_count={selection.summary['selected_reference_row_count']}")
    print(f"surface_density_per_deg2={selection.summary['surface_density_per_deg2']}")


if __name__ == "__main__":
    main()
