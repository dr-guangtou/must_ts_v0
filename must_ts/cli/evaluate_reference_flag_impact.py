"""CLI for evaluating HSC flag impact on reference-selected objects."""

from __future__ import annotations

import argparse
from pathlib import Path

from must_ts.catalogs.registry import CatalogContract
from must_ts.qa.flag_impact import (
    FlagImpactConfig,
    evaluate_reference_flag_impact,
    write_flag_impact_result,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate candidate photometric flags on reference-selected objects."
    )
    parser.add_argument("photometric_catalog_yaml", type=Path)
    parser.add_argument("footprint")
    parser.add_argument("reference_selection_path", type=Path)
    parser.add_argument("flag_config_yaml", type=Path)
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

    photometric_contract = CatalogContract.from_yaml(
        args.photometric_catalog_yaml,
        repo_root=args.repo_root,
    )
    flag_config = FlagImpactConfig.from_yaml(args.flag_config_yaml)
    footprint = photometric_contract.footprints[args.footprint]
    result = evaluate_reference_flag_impact(
        photometric_contract=photometric_contract,
        reference_selection_path=args.reference_selection_path,
        flag_config=flag_config,
        footprint=footprint,
        tract_ids=args.tract_ids,
        max_partitions=args.max_partitions,
    )
    run_name = args.run_name or f"{flag_config.name}_{footprint.name}"
    run_root = write_flag_impact_result(
        result=result,
        output_root=args.output_root,
        run_name=run_name,
        repo_root=args.repo_root,
    )
    print(f"run_root={run_root}")
    print(f"joined_row_count={result.summary['joined_row_count']}")
    print(f"any_candidate_flagged_count={result.summary['any_candidate_flagged_count']}")
    print(f"any_candidate_flagged_fraction={result.summary['any_candidate_flagged_fraction']}")


if __name__ == "__main__":
    main()
