# VIBE-CODED
"""Build llms.txt — a single catalog of the site for AI agents.

Output: `afterpython/_website/static/llms.txt`. SvelteKit's static adapter
serves it at `/llms.txt` so agents (Claude, GPT, etc.) can fetch a curated
overview of the project + a link list of every published page.

Conforms to the llms.txt convention (https://llmstxt.org/): a markdown file
with a project H1, optional context paragraphs, and `## Section` headings
each containing a link list.

Flow
----
build_llms_txt()                                      # entry point
  ├─ _read_readme() + _standardize_readme()           # → header content
  └─ for each content_type in ORDERED_CONTENT_TYPES:
       └─ _list_pages(content_type)                    # → [(title, url, abstract)]
            (skips entries whose source .md no longer exists — those were
             auto-generated placeholder index.md files deleted in postbuild)
       └─ _format_section(content_type, blurb, entries)
            ├─ heading: SECTION_HEADINGS[content_type]
            ├─ blurb:   project.description from afterpython/{type}/myst.yml
            └─ entries: `- [Title](/type/slug.md): abstract`
"""

from __future__ import annotations

import json
import re

import click

import afterpython as ap
from afterpython._typing import tContentType
from afterpython.const import CONTENT_TYPES

# A line whose entire content is a markdown image (badge), with optional
# link wrapper and optional HTML-comment wrapper.
#   matches: ![alt](url)
#            [![alt](url)](link)
#            <!-- ![alt](url) -->
#            <!-- [![alt](url)](link) -->
# Anchored ^...$ so inline references in body prose are NOT matched.
_BADGE_LINE = re.compile(
    r"""
    ^\s*                # leading whitespace
    (?:<!--\s*)?        # optional HTML comment open
    \[?                 # optional link open  '['
    !\[[^\]]*\]         # ![alt]
    \([^)]+\)           # (image_url)
    (?:\]\([^)]+\))?    # optional  ](link_url)
    (?:\s*-->)?         # optional HTML comment close
    \s*$                # trailing whitespace
    """,
    re.VERBOSE,
)

# Order in which content-type sections appear in llms.txt. Sections with zero
# entries are skipped. Reasoning: an agent answering "how do I X?" should hit
# concepts first (doc), then how-to (tutorial/guide), then examples, then
# background (blog) — strongest signal first.
ORDERED_CONTENT_TYPES: list[tContentType] = [
    "doc",
    "tutorial",
    "guide",
    "example",
    "blog",
]

# One-line hint that sits between the README and the section list, telling
# an LLM reading llms.txt that the URLs below are fetchable markdown sources
# (the Mintlify / Anthropic-docs convention). Costs ~20 tokens and removes
# any ambiguity about what fetching `/doc/quickstart.md` returns.
LINK_NOTE = (
    "> Every link below points to the raw markdown source of the page."
    " Fetch any URL directly to read its content as markdown."
)

# Human-readable display name for each content type's `## ` heading in llms.txt.
SECTION_HEADINGS: dict[tContentType, str] = {
    "doc": "Documentation",
    "tutorial": "Tutorials",
    "guide": "Guides",
    "example": "Examples",
    "blog": "Blog",
}

# Defensive sync check: if a new content type is added to const.CONTENT_TYPES,
# the developer must remember to slot it into ORDERED_CONTENT_TYPES and
# SECTION_HEADINGS. Import-time failure beats a silently-missing section.
assert set(ORDERED_CONTENT_TYPES) == CONTENT_TYPES, (
    "ORDERED_CONTENT_TYPES is out of sync with const.CONTENT_TYPES"
)
assert set(SECTION_HEADINGS.keys()) == CONTENT_TYPES, (
    "SECTION_HEADINGS is out of sync with const.CONTENT_TYPES"
)


def _read_readme() -> str:
    """Read the project's README.md from repo root, verbatim. Empty string if
    the README is missing (e.g. brand new project)."""
    readme_path = ap.paths.user_path / "README.md"
    if not readme_path.exists():
        return ""
    return readme_path.read_text(encoding="utf-8")


def _standardize_readme(text: str) -> str:
    """Clean the README before embedding it in llms.txt.

    Currently strips badges (shields, download counters, etc.) from the
    README's *header zone* — everything before the first `## ` heading —
    since they're chrome for human readers and noise for LLMs.

    The header-zone restriction protects content images that legitimately
    appear later in the README (e.g. the `<picture>` website screenshot
    after the first H2 — also untouched because it's HTML, not a markdown
    image).

    Future ideas if more cleanup is wanted: strip GitHub-flavored anchor
    links, install commands, "table of contents" sections.
    """
    lines = text.split("\n")

    # Boundary of the header zone: index of the first `## ` line, or end of
    # file if no H2 exists.
    boundary = next(
        (i for i, line in enumerate(lines) if line.startswith("## ")),
        len(lines),
    )

    cleaned_header = [line for line in lines[:boundary] if not _BADGE_LINE.match(line)]
    rejoined = "\n".join(cleaned_header + lines[boundary:])

    # After removing 9 consecutive badge lines, you can end up with a stack
    # of blanks where they used to be. Collapse 3+ newlines to 2 (one blank).
    return re.sub(r"\n{3,}", "\n\n", rejoined)


def _read_section_blurb(content_type: tContentType) -> str | None:
    """Pull the section's one-line blurb from `afterpython/{type}/myst.yml`'s
    `project.description`.

    Returns None if myst.yml is missing or has no description set — in which
    case the section in llms.txt simply omits the `> blurb` line.
    """
    from afterpython._io.yaml import read_yaml

    myst_yml = ap.paths.afterpython_path / content_type / "myst.yml"
    if not myst_yml.exists():
        return None

    data = read_yaml(myst_yml) or {}
    description = data.get("project", {}).get("description")
    return str(description).strip() if description else None


def _list_pages(content_type: tContentType) -> list[tuple[str, str, str | None]]:
    """Return `[(title, url, abstract), ...]` for each page MyST built.

    Reads MyST's `_build/site/content/*.json` files (which already have
    title, slug, and frontmatter resolved — no need to re-parse source).
    Skips entries whose source .md no longer exists; those were auto-generated
    placeholder index.md files that `delete_placeholder_index_md_files`
    removed at the start of postbuild.
    """
    content_dir = ap.paths.afterpython_path / content_type
    myst_content_dir = content_dir / "_build" / "site" / "content"
    if not myst_content_dir.exists():
        return []

    pages: list[tuple[str, str, str | None]] = []
    for json_file in sorted(myst_content_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        # Filter placeholder index.md entries: their source has been deleted.
        location = data.get("location", "")
        source_md = content_dir / location.lstrip("/")
        if not source_md.exists():
            continue

        slug = data.get("slug")
        if not slug:
            continue

        frontmatter = data.get("frontmatter", {})
        title = frontmatter.get("title") or slug
        abstract = frontmatter.get("abstract")

        url = f"/{content_type}/{slug}.md"
        pages.append((title, url, abstract))
    return pages


def _format_link_entry(title: str, url: str, abstract: str | None) -> str:
    """One line of the link list.

    With abstract:    `- [Title](url): abstract`
    Without abstract: `- [Title](url)`
    """
    if abstract:
        return f"- [{title}]({url}): {abstract.strip()}"
    return f"- [{title}]({url})"


def _format_section(
    content_type: tContentType,
    blurb: str | None,
    entries: list[tuple[str, str, str | None]],
) -> str:
    """Format one `## Section`: heading, optional blurb, link list."""
    parts = [f"## {SECTION_HEADINGS[content_type]}", ""]
    if blurb:
        parts.extend([f"> {blurb}", ""])
    for title, url, abstract in entries:
        parts.append(_format_link_entry(title, url, abstract))
    return "\n".join(parts)


def build_llms_txt() -> None:
    """Generate `_website/static/llms.txt` — one catalog file for the site.

    Runs at the end of `postbuild()` after MyST output is finalized and
    placeholder index.md files have been removed.
    """
    readme = _standardize_readme(_read_readme())

    sections: list[str] = []
    total_entries = 0
    for content_type in ORDERED_CONTENT_TYPES:
        entries = _list_pages(content_type)
        if not entries:
            continue
        blurb = _read_section_blurb(content_type)
        sections.append(_format_section(content_type, blurb, entries))
        total_entries += len(entries)

    body = readme.rstrip()
    if sections:
        body = body + "\n\n" + LINK_NOTE + "\n\n" + "\n\n".join(sections) + "\n"

    output = ap.paths.website_path / "static" / "llms.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body, encoding="utf-8")
    click.echo(f"Generated {output} ({total_entries} entries)")
