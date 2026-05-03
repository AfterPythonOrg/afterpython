# VIBE-CODED
"""Publish raw markdown alongside rendered HTML.

For every page the website serves at `/{type}/{slug}`, also publish the source
markdown at `/{type}/{slug}.md`. Lets LLMs and AI agents fetch clean content
without HTML chrome (the Mintlify / Anthropic-docs pattern).

Output goes into `afterpython/_website/static/{type}/{slug}.md`. SvelteKit's
static adapter then serves each file at the matching URL with no SvelteKit-side
code changes.

Flow
----
build_url_md()                                        # entry point
  └─ for each content_type in CONTENT_TYPES:
       └─ for each `*.md` / `*.ipynb` under afterpython/{type}/:
            ├─ _slugify(stem)                         → URL slug
            ├─ .md    → shutil.copy(source, dest)    (frontmatter preserved)
            └─ .ipynb → jupytext.read + write(fmt="md") (cell outputs stripped)
"""

from __future__ import annotations

import shutil
from pathlib import Path

import click
import jupytext

import afterpython as ap
from afterpython._typing import tContentType
from afterpython.const import CONTENT_TYPES


def _slugify(stem: str) -> str:
    """Mirror MyST's URL slug rule so each `.md` lands at the same URL as its
    rendered HTML sibling.

    `package_management.md` -> `/doc/package-management.md`
    `CONTRIBUTING.md`       -> `/doc/contributing.md`
    """
    return stem.lower().replace("_", "-")


def _publish_md(source: Path, dest: Path) -> None:
    """Copy a `.md` source verbatim. Frontmatter is preserved — LLMs can use
    it (date, authors, tags) and it's harmless if ignored.
    """
    shutil.copy(source, dest)


def _publish_ipynb(source: Path, dest: Path) -> None:
    """Convert a notebook to clean markdown via jupytext.

    jupytext strips cell outputs by default, producing a leaner file than
    `nbconvert` would. The `md` format is jupytext's default — clean enough
    for LLM consumption while still round-trippable if anyone needs the
    notebook back.
    """
    notebook = jupytext.read(source)
    jupytext.write(notebook, dest, fmt="md")


def _publish_for_type(content_type: tContentType) -> int:
    """Walk one content type's source dir; publish every supported file.
    Returns the number of files written.
    """
    source_dir = ap.paths.afterpython_path / content_type
    if not source_dir.exists():
        return 0

    dest_dir = ap.paths.website_path / "static" / content_type
    dest_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for source in sorted(source_dir.rglob("*")):
        if "_build" in source.parts:
            continue
        if not source.is_file():
            continue

        slug = _slugify(source.stem)
        dest = dest_dir / f"{slug}.md"

        if source.suffix == ".md":
            _publish_md(source, dest)
        elif source.suffix == ".ipynb":
            _publish_ipynb(source, dest)
        else:
            continue

        count += 1
    return count


def build_url_md() -> None:
    """Publish raw markdown for every content type alongside the rendered HTML.

    Runs as part of `postbuild()` after MyST's HTML has been copied into
    `_website/static/{type}/`. Each `.md` ends up as a sibling of the rendered
    `{slug}/index.html`, served at `/{type}/{slug}.md` by SvelteKit's static
    adapter.
    """
    for content_type in CONTENT_TYPES:
        count = _publish_for_type(content_type)
        if count > 0:
            click.echo(f"Published {count} url-md file(s) for {content_type}/")
