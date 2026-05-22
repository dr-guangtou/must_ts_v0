"""CLI for production selection runs."""

from must_ts.cli.evaluate_recipe import run_cli


def main() -> None:
    run_cli(description="Run a MUST target-selection production config.")


if __name__ == "__main__":
    main()
