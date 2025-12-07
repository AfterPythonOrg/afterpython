from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from afterpython._typing import NodeEnv, tContentType

import subprocess

import afterpython as ap
from afterpython._io.yaml import read_yaml, write_yaml
from afterpython.utils import deep_merge


def update_authors_yml(data_update: dict):
    """Update authors.yml while preserving order and formatting"""
    file_path = ap.paths.afterpython_path / "authors.yml"

    if not file_path.exists():
        write_yaml(file_path, data_update)
        return

    existing_data = read_yaml(file_path) or {}

    # merge authors, keep the author with more fields (e.g. github, x, etc.) to avoid duplication
    merged_authors = {}
    for author in (
        existing_data["project"]["contributors"]
        + data_update["project"]["contributors"]
    ):
        author_id = author["id"]
        if author_id not in merged_authors:
            merged_authors[author_id] = author
        else:
            # keep the author with more fields (e.g. github, x, etc.)
            if len(author.keys()) > len(merged_authors[author_id].keys()):
                merged_authors[author_id] = author
    existing_data["project"]["contributors"] = list(merged_authors.values())

    # set comments for project section for convenience
    if "project" in existing_data and not existing_data["project"].ca.items.get(
        "contributors"
    ):
        existing_data["project"].yaml_set_comment_before_after_key(
            "contributors",
            before="See more at: https://mystmd.org/guide/frontmatter#frontmatter-authors",
        )
    write_yaml(file_path, existing_data)


def update_myst_yml(data_update: dict, path: Path, add_comments: bool = False):
    """Update myst.yml while preserving order and formatting

    Args:
        data_update: dict of data to update
        path: path to the myst.yml file, e.g. doc/, blog/, tutorial/, example/, guide/
    """

    file_path = path / "myst.yml"

    if not file_path.exists():
        raise FileNotFoundError(
            f"myst.yml not found at {file_path}, did you forget to run `ap init` or `myst init`?"
        )

    existing_data = read_yaml(file_path) or {}
    existing_data = deep_merge(existing_data, data_update, extend_lists=False)

    # NOTE: this checking existing_data["key1"].ca.items.get("key2") is buggy
    # only add_comments=True during init to avoid adding duplicate comments
    if add_comments:
        # set comments for project section for convenience
        if "project" in existing_data:
            if not existing_data["project"].ca.items.get("id"):
                existing_data["project"].yaml_set_comment_before_after_key(
                    "id",
                    before="See how to create Table of Contents at: https://mystmd.org/guide/table-of-contents",
                )
            if not existing_data["project"].ca.items.get("authors"):
                existing_data["project"].yaml_set_comment_before_after_key(
                    "authors",
                    before="See more authors' fields at: https://mystmd.org/guide/frontmatter#frontmatter-authors",
                )
            if not existing_data["project"].ca.items.get("venue"):
                existing_data["project"].yaml_set_comment_before_after_key(
                    "venue",
                    before="See more venue's fields at: https://mystmd.org/guide/frontmatter#venue",
                )
        if "site" in existing_data:
            if not existing_data["site"].ca.items.get("options"):
                existing_data["site"].yaml_set_comment_before_after_key(
                    "options",
                    before="See options at: https://mystmd.org/guide/website-templates#site-options",
                )
            if not existing_data["site"].ca.items.get("actions"):
                existing_data["site"].yaml_set_comment_before_after_key(
                    "actions",
                    before="See web layout at: https://mystmd.org/guide/website-navigation",
                )

    write_yaml(file_path, existing_data)


def _write_index_file(content_type: tContentType):
    """Create a placeholder index.md file for MyST to prevent first file from becoming index.

    MyST treats the first file in TOC as index. This placeholder ensures all actual
    content files get proper slugs. The generated index.html is deleted post-build
    since SvelteKit owns the landing page route.

    Note: This only creates the file. TOC modification is handled by the build process.

    Raises:
        FileExistsError: If index.md already exists (users shouldn't create this file).
    """
    if content_type == "doc":
        return  # Doc doesn't need a placeholder index.md

    content_path = ap.paths.afterpython_path / content_type
    index_file = content_path / "index.md"

    # Check if user created an index.md file
    if index_file.exists():
        raise FileExistsError(
            f"\n"
            f"Found existing 'index.md' in afterpython/{content_type}/\n"
            f"\n"
            f"The 'index.md' file is reserved for internal use by AfterPython.\n"
            f"MyST treats the first file in TOC as index, which would conflict with\n"
            f"SvelteKit (project-website-template)'s landing page route (/{content_type}).\n"
            f"\n"
            f"Please rename your file to something else (e.g., '{content_type}_intro.md')\n"
            f"and update the reference in afterpython/{content_type}/myst.yml"
        )

    index_content = f"""---
title: ← {content_type.capitalize()}
---

This is a placeholder index page. The actual {content_type} landing page is rendered by SvelteKit.
"""
    index_file.write_text(index_content)
    return index_file


def _write_welcome_file(content_type: tContentType):
    welcome_file = ap.paths.afterpython_path / content_type / "index.md"
    if welcome_file.exists():
        return
    welcome_content = f"""# Welcome to AfterPython

Welcome to your project's {content_type}! This is a starter page to help you get started.

## Getting Started

Replace this placeholder content with your own. Here's what you can do:

- Creating new `.md` or `.ipynb` files in the `afterpython/{content_type}/` directory
- Writing in MyST Markdown format
- Adding images to the `afterpython/static/` directory and referencing them

## Resources

- [AfterPython's Project Website](https://afterpython.afterpython.org)
- [MyST Markdown Guide](https://mystmd.org)

Start building your amazing project! 🚀
"""
    welcome_file.write_text(welcome_content)
    return welcome_file


def init_myst():
    """
    Initialize MyST Markdown (mystmd) and myst.yml files in
    doc/, blog/, tutorial/, example/, guide/ directories with sensible defaults
    """
    from afterpython.const import CONTENT_TYPES
    from afterpython.utils import find_node_env

    # find any existing node.js version and use it, if no, install the Node.js version specified in NODEENV_VERSION
    node_env: NodeEnv = find_node_env()
    subprocess.run(["npm", "install", "-g", "pnpm"], env=node_env, check=True)
    for content_type in CONTENT_TYPES:
        path = ap.paths.afterpython_path / content_type
        print(f"Initializing MyST Markdown (mystmd) in {path.name}/ directory ...")
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["myst", "init"], cwd=path, input="n\n", text=True, env=node_env)
        myst_yml_defaults = {
            "extends": "../authors.yml",
            "project": {
                "license": "CC-BY-4.0",
                "subject": content_type.capitalize()
                if content_type != "doc"
                else "Documentation",
            },
            "site": {
                "options": {
                    "analytics_google": "{{ GOOGLE_ANALYTICS_ID }}",
                    # "twitter": "",
                },
            },
        }
        update_myst_yml(myst_yml_defaults, path, add_comments=True)
        _write_welcome_file(content_type)
    subprocess.run(["ap", "sync"])
