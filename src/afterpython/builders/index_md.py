import click

import afterpython as ap
from afterpython.const import CONTENT_TYPES


def create_placeholder_index_md_files():
    """Create placeholder index.md files for non-doc content types.

    Without these placeholders, MyST treats the first file in TOC as index,
    causing it to use routes like /blog instead of /blog/blog1. These routes
    are reserved for SvelteKit landing pages. Placeholders ensure all actual
    content files get proper slugs and are deleted post-build.
    """
    from afterpython._io.yaml import read_yaml, write_yaml
    from afterpython.tools.myst import _write_index_file

    for content_type in CONTENT_TYPES:
        if content_type == "doc":
            continue  # Doc doesn't need a placeholder index.md

        content_path = ap.paths.afterpython_path / content_type
        if not content_path.exists():
            click.echo(
                f"No content found in {content_path}, skip creating placeholder index.md"
            )
            continue

        myst_yml_path = content_path / "myst.yml"
        if not myst_yml_path.exists():
            click.echo(
                f"No myst.yml found in {content_path}, skip creating placeholder index.md"
            )
            continue

        content_path = ap.paths.afterpython_path / content_type
        myst_yml_path = content_path / "myst.yml"

        # Prepend index.md to TOC in myst.yml
        if myst_yml_path.exists():
            # Create placeholder index.md file
            _write_index_file(content_type)
            myst_data = read_yaml(myst_yml_path) or {}
            toc = myst_data.get("project", {}).get("toc", [])

            # Check if index.md is already first in TOC
            if not toc or toc[0].get("file") != "index.md":
                # Prepend index.md to TOC in myst.yml
                new_toc = [{"file": "index.md"}, *toc]
                if "project" not in myst_data:
                    myst_data["project"] = {}
                myst_data["project"]["toc"] = new_toc
                write_yaml(myst_yml_path, myst_data)
                click.echo(f"Added index.md to TOC in {myst_yml_path}")


def delete_placeholder_index_md_files():
    """Delete placeholder index.md and built index.html for non-doc content types.

    These files were created pre-build to ensure proper slug generation. Now that
    MyST has built the content with correct slugs, we delete them so SvelteKit
    can own the landing page routes (/blog, /tutorial, etc.) in the project website.
    """
    from afterpython._io.yaml import read_yaml, write_yaml

    for content_type in CONTENT_TYPES:
        if content_type == "doc":
            continue  # Doc doesn't need a placeholder index.md

        content_path = ap.paths.afterpython_path / content_type
        myst_yml_path = content_path / "myst.yml"
        index_md = content_path / "index.md"

        # Delete index.md from source
        if index_md.exists():
            index_md.unlink()
            click.echo(f"Deleted: {index_md}")

        # Delete index.html from build output
        index_html = content_path / "_build" / "html" / "index.html"
        if index_html.exists():
            index_html.unlink()
            click.echo(f"Deleted: {index_html}")

        # Remove index.md from TOC in myst.yml
        if myst_yml_path.exists():
            myst_data = read_yaml(myst_yml_path) or {}
            toc = myst_data.get("project", {}).get("toc", [])

            # Remove index.md from TOC if it's the first entry
            if toc and toc[0].get("file") == "index.md":
                myst_data["project"]["toc"] = toc[1:]
                write_yaml(myst_yml_path, myst_data)
                click.echo(f"Removed index.md from TOC in {myst_yml_path}")
