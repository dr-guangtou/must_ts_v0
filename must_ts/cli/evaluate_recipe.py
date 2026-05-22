"""CLI for evaluation runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from must_ts.selection.engine import run_configured_selection


def run_cli(*, description: str) -> None:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("run_config", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = run_configured_selection(args.run_config, repo_root=args.repo_root)
    print(result["run_root"])


def main() -> None:
    run_cli(description="Run a MUST target-selection evaluation config.")


if __name__ == "__main__":
    main()
