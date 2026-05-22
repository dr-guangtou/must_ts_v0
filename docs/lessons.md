# Lessons

Last updated: 2026-05-22

## 2026-05-22

- This repository started without prior local lesson notes. Future mistakes, surprising data behavior, and durable rationale should be recorded here as they occur.
- The current HSC input is an assembled local catalog built by `hsc_sandbox`, not a direct live view of the HSC database. Project code should depend on a documented dataset label and manifest path, not hard-code assumptions about all future photometric inputs.
- Catalog manifests are not guaranteed to share the same metadata columns. The HSC reference manifest has `row_count`, while the current HSC photometric manifest does not, so code should require only the configured path and tract columns.
- Command examples should match the installed script names in `pyproject.toml`; this project currently uses `must-inspect-catalog`, `must-evaluate-recipe`, and `must-select-targets`.
