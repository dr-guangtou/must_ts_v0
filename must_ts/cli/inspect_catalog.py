"""CLI for inspecting a catalog contract."""

from __future__ import annotations

import argparse
from pathlib import Path

from must_ts.catalogs.readers import load_manifest
from must_ts.catalogs.registry import CatalogContract


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a MUST catalog contract.")
    parser.add_argument("catalog_yaml", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    contract = CatalogContract.from_yaml(args.catalog_yaml, repo_root=args.repo_root)
    manifest = load_manifest(contract)
    print(f"name={contract.name}")
    print(f"kind={contract.kind}")
    print(f"manifest_rows={len(manifest)}")
    print(f"path_column={contract.path_column}")


if __name__ == "__main__":
    main()
