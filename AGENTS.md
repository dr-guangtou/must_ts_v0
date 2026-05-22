# Agent Core Mandates

These rules apply to this repository.

## Principles

- Use English for code, documentation, commit messages, and logs.
- Do not work directly on `main`. Create a feature branch before changing files.
- Keep `docs/SPEC.md` as the source of truth for architecture and data contracts.
- Validate at small scale before full execution. Use measured values, not estimates.
- Persist new durable rules in this file immediately.
- This repository is only for organization, investigation, bookkeeping, code, contracts, recipes, and documentation. Do not store catalogs or large generated data in Git.
- On this machine, MUST target-selection generated products must live outside the repo under `/Volumes/galaxy/must/target_selection/`, not under `/Volumes/galaxy/hsc/`.

## Workflow

- Review `docs/lessons.md` at session start.
- Track active work in `docs/todo.md` and add a review section when done.
- Before writing new code, inspect similar files and follow local patterns.
- Use `uv` for Python dependency management and command execution.
- Use Ruff through pre-commit as the formatting and linting source of truth.

## Style

- Use `snake_case` names in Python and general code. Do not use `camelCase`.
- Use specific, complete names that make sense to readers new to the project.
- Avoid comments that only restate names or obvious operations.
