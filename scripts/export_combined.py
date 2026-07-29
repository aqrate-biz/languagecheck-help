#!/usr/bin/env python3
"""Combine MkDocs pages into a single Markdown file in nav order."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+", re.MULTILINE)


class _MkDocsLoader(yaml.SafeLoader):
    """YAML loader that tolerates MkDocs python-name tags."""


def _construct_undefined(loader: yaml.Loader, node: yaml.Node) -> Any:
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


_MkDocsLoader.add_constructor(None, _construct_undefined)


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=_MkDocsLoader)


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-") or "section"


def iter_nav(
    nav: list[Any],
    *,
    depth: int = 1,
) -> list[tuple[int, str, str | None]]:
    """Flatten nav into (depth, title, file_or_none) entries."""
    entries: list[tuple[int, str, str | None]] = []
    for item in nav:
        if isinstance(item, str):
            title = Path(item).stem.replace("-", " ").replace("_", " ").title()
            entries.append((depth, title, item))
            continue
        if not isinstance(item, dict):
            continue
        for title, value in item.items():
            if isinstance(value, str):
                entries.append((depth, title, value))
            elif isinstance(value, list):
                entries.append((depth, title, None))
                entries.extend(iter_nav(value, depth=depth + 1))
    return entries


def strip_front_matter(content: str) -> str:
    return FRONT_MATTER_RE.sub("", content, count=1)


def shift_headings(content: str, shift: int) -> str:
    if shift <= 0:
        return content

    def replacer(match: re.Match[str]) -> str:
        level = len(match.group(1))
        new_level = min(level + shift, 6)
        return "#" * new_level + " "

    return HEADING_RE.sub(replacer, content)


def remove_leading_title(content: str, title: str) -> str:
    """Drop a leading H1 that matches the nav title to avoid duplicates."""
    pattern = re.compile(
        rf"^#\s+{re.escape(title)}\s*\n+",
        re.IGNORECASE,
    )
    return pattern.sub("", content.lstrip(), count=1)


def read_page(docs_dir: Path, rel_path: str) -> str:
    path = docs_dir / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Missing page referenced in nav: {rel_path}")
    return path.read_text(encoding="utf-8")


def build_combined_markdown(
    *,
    config_path: Path,
    site_name: str | None = None,
    toc_title: str = "Table of Contents",
    include_toc: bool = True,
) -> str:
    config = load_config(config_path)
    docs_dir = config_path.parent / config.get("docs_dir", "docs")
    nav = config.get("nav") or []
    title = site_name or config.get("site_name") or "Documentation"

    entries = iter_nav(nav)
    used_anchors: dict[str, int] = {}
    toc_lines: list[str] = []
    body_parts: list[str] = []

    def unique_anchor(label: str) -> str:
        base = slugify(label)
        count = used_anchors.get(base, 0)
        used_anchors[base] = count + 1
        return base if count == 0 else f"{base}-{count}"

    for depth, nav_title, rel_path in entries:
        anchor = unique_anchor(nav_title)
        indent = "  " * (depth - 1)
        toc_lines.append(f"{indent}- [{nav_title}](#{anchor})")

        heading = "#" * min(depth, 6)
        section = [f'{heading} {nav_title} {{#{anchor}}}', ""]

        if rel_path:
            raw = strip_front_matter(read_page(docs_dir, rel_path))
            raw = remove_leading_title(raw, nav_title)
            # Keep page-internal headings below the nav heading.
            raw = shift_headings(raw.strip(), shift=depth)
            if raw:
                section.append(raw)
                section.append("")

        body_parts.append("\n".join(section).rstrip() + "\n")

    parts = [f"# {title}", ""]
    if include_toc and toc_lines:
        parts.extend([f"## {toc_title}", "", *toc_lines, "", "---", ""])
    parts.extend(body_parts)
    return "\n".join(parts).rstrip() + "\n"


PDF_CSS = """
@page {
  size: A4;
  margin: 20mm 18mm 22mm 18mm;
  @bottom-center {
    content: counter(page);
    font-size: 9pt;
    color: #666;
  }
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.45;
  color: #222;
}
h1, h2, h3, h4, h5, h6 {
  color: #1a237e;
  page-break-after: avoid;
}
h1 { font-size: 22pt; margin-top: 0; }
h2 { font-size: 16pt; border-bottom: 1px solid #ddd; padding-bottom: 0.2em; }
h3 { font-size: 13pt; }
h4 { font-size: 11.5pt; }
a { color: #283593; text-decoration: none; }
code, pre {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 9pt;
}
pre {
  background: #f6f8fa;
  padding: 0.75em 1em;
  border-radius: 4px;
  white-space: pre-wrap;
  page-break-inside: avoid;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
  font-size: 9.5pt;
}
th, td {
  border: 1px solid #ccc;
  padding: 0.35em 0.5em;
  text-align: left;
}
blockquote {
  border-left: 3px solid #c5cae9;
  margin-left: 0;
  padding-left: 1em;
  color: #555;
}
hr { border: none; border-top: 1px solid #ddd; margin: 1.5em 0; }
img { max-width: 100%; }
"""


def write_combined_markdown(
    *,
    config_path: Path,
    output_path: Path,
    site_name: str | None = None,
    toc_title: str = "Table of Contents",
    include_toc: bool = True,
) -> Path:
    content = build_combined_markdown(
        config_path=config_path,
        site_name=site_name,
        toc_title=toc_title,
        include_toc=include_toc,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def markdown_to_html(markdown_text: str, *, title: str) -> str:
    import markdown as md

    body = md.markdown(
        markdown_text,
        extensions=[
            "attr_list",
            "tables",
            "fenced_code",
            "sane_lists",
            "admonition",
            "toc",
        ],
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{title}</title>\n"
        f"  <style>{PDF_CSS}</style>\n"
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )


def write_combined_pdf(
    *,
    markdown_path: Path,
    output_path: Path,
    title: str = "Documentation",
) -> Path:
    try:
        from weasyprint import HTML
    except OSError as exc:
        raise SystemExit(
            "WeasyPrint system libraries are missing (pango/cairo).\n"
            "Install them, then reinstall PDF deps:\n"
            "  macOS:  brew install pango cairo gdk-pixbuf libffi\n"
            "  Ubuntu: sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 "
            "libgdk-pixbuf2.0-0 libffi-dev shared-mime-info\n"
            "  pip install -r requirements-pdf.txt"
        ) from exc
    except ImportError as exc:
        raise SystemExit(
            "WeasyPrint is not installed. Run:\n"
            "  pip install -r requirements-pdf.txt"
        ) from exc

    markdown_text = markdown_path.read_text(encoding="utf-8")
    html = markdown_to_html(markdown_text, title=title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(markdown_path.parent)).write_pdf(output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export all MkDocs pages into one Markdown (and optional PDF).",
    )
    parser.add_argument(
        "-f",
        "--config",
        default="mkdocs.yml",
        type=Path,
        help="Path to mkdocs.yml (default: ./mkdocs.yml)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="export/languagecheck-help.md",
        type=Path,
        help="Output Markdown path (default: export/languagecheck-help.md)",
    )
    parser.add_argument(
        "--pdf",
        nargs="?",
        const="export/languagecheck-help.pdf",
        default=None,
        type=Path,
        help="Also write a PDF (default path: export/languagecheck-help.pdf)",
    )
    parser.add_argument(
        "--toc-title",
        default="Table of Contents",
        help="Title for the generated table of contents",
    )
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Do not include a table of contents",
    )
    args = parser.parse_args()

    config_path = args.config.resolve()
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    config = load_config(config_path)
    site_name = config.get("site_name") or "Documentation"

    output = write_combined_markdown(
        config_path=config_path,
        output_path=args.output.resolve(),
        site_name=site_name,
        toc_title=args.toc_title,
        include_toc=not args.no_toc,
    )
    print(f"Wrote {output}")

    if args.pdf is not None:
        pdf_path = write_combined_pdf(
            markdown_path=output,
            output_path=args.pdf.resolve(),
            title=site_name,
        )
        print(f"Wrote {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
