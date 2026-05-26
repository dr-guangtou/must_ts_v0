"""Build the review PDF from the markdown source.

Reads ``docs/review/must_ts_v0_review.md`` and writes
``docs/review/must_ts_v0_review.pdf`` next to it, using the pure-Python
``markdown-pdf`` package. Run with:

    uv run --with markdown-pdf python scripts/build_review_pdf.py

The script intentionally has no behavior beyond converting one specific
markdown file to PDF. It exists so the conversion is reproducible without
relying on a system-wide pandoc install.
"""

from __future__ import annotations

import re
from pathlib import Path

from markdown_pdf import MarkdownPdf, Section

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKDOWN_PATH = REPO_ROOT / "docs" / "review" / "must_ts_v0_review.md"
PDF_PATH = REPO_ROOT / "docs" / "review" / "must_ts_v0_review.pdf"

PAGE_CSS = """
body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10.5pt;
       line-height: 1.4; color: #1c1c1c; }
h1   { font-size: 20pt; margin-top: 0.8em; margin-bottom: 0.4em;
       border-bottom: 1px solid #888; padding-bottom: 0.2em; }
h2   { font-size: 14pt; margin-top: 0.8em; margin-bottom: 0.3em; color: #2a4d7a; }
h3   { font-size: 12pt; margin-top: 0.7em; margin-bottom: 0.2em; color: #444; }
p    { margin: 0.4em 0; text-align: justify; }
code { font-family: 'Menlo', 'Consolas', monospace; font-size: 9.5pt;
       background: #f2f2f2; padding: 0 2px; }
pre  { font-family: 'Menlo', 'Consolas', monospace; font-size: 9pt;
       background: #f5f5f5; border: 1px solid #ddd; padding: 6px 8px;
       border-radius: 3px; white-space: pre-wrap; }
table { border-collapse: collapse; margin: 0.5em 0; font-size: 9.5pt; }
th, td { border: 1px solid #bbb; padding: 3px 6px; }
th     { background: #ececec; text-align: left; }
blockquote { border-left: 3px solid #ccc; margin: 0.5em 0; padding: 0 0.8em;
             color: #444; }
"""


def _strip_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract the YAML front matter and return (metadata, body)."""
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if match is None:
        return {}, text
    metadata = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, match.group(2)


def _title_block(metadata: dict[str, str]) -> str:
    """Build a small markdown title block from the YAML front matter."""
    parts: list[str] = []
    title = metadata.get("title")
    subtitle = metadata.get("subtitle")
    author = metadata.get("author")
    date = metadata.get("date")
    if title:
        parts.append(f"# {title}")
    if subtitle:
        parts.append(f"*{subtitle}*")
    meta_line_bits = [part for part in (author, date) if part]
    if meta_line_bits:
        parts.append(" — ".join(meta_line_bits))
    return "\n\n".join(parts) + "\n\n"


def main() -> None:
    if not MARKDOWN_PATH.exists():
        raise FileNotFoundError(f"missing review markdown: {MARKDOWN_PATH}")

    raw = MARKDOWN_PATH.read_text()
    metadata, body = _strip_frontmatter(raw)
    composed = _title_block(metadata) + body

    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.meta["title"] = metadata.get("title", "MUST Target Selection Review")
    pdf.meta["author"] = metadata.get("author", "MUST target-selection development")
    pdf.add_section(Section(composed, paper_size="A4"), user_css=PAGE_CSS)
    pdf.save(PDF_PATH)
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    main()
