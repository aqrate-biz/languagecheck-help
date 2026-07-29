"""MkDocs hook: export all pages into a single Markdown file after build."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from export_combined import write_combined_markdown  # noqa: E402


def on_post_build(config, **kwargs) -> None:
    """Write a nav-ordered Markdown export into the site directory."""
    site_dir = Path(config["site_dir"])
    config_file = Path(config["config_file_path"])
    output_path = site_dir / "export" / "languagecheck-help.md"

    write_combined_markdown(
        config_path=config_file,
        output_path=output_path,
        site_name=config.get("site_name"),
        toc_title="Table of Contents",
        include_toc=True,
    )
    print(f"INFO    -  Combined Markdown export written to {output_path}")
