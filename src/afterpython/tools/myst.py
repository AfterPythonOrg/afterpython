from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from afterpython._typing import NodeEnv, tContentType

import subprocess

import click

import afterpython as ap
from afterpython._io.yaml import read_yaml, write_yaml
from afterpython.const import PLACEHOLDER_INDEX_MARKER
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
        click.ClickException: If a non-placeholder index.md already exists.
    """
    if content_type == "doc":
        return  # Doc doesn't need a placeholder index.md

    content_path = ap.paths.afterpython_path / content_type
    index_file = content_path / "index.md"

    # Check if user created an index.md file
    if index_file.exists():
        existing_content = index_file.read_text(encoding="utf-8", errors="ignore")
        if PLACEHOLDER_INDEX_MARKER in existing_content:
            return index_file

        raise click.ClickException(
            f"\n"
            f"Found existing 'afterpython/{content_type}/index.md'\n"
            f"\n"
            f"'afterpython/{content_type}/index.md' is reserved for internal use by AfterPython.\n"
            f"MyST treats the first file in TOC as index, which would conflict with\n"
            f"the SvelteKit listing page route '/{content_type}', which is owned by\n"
            f"AfterPython's project website.\n"
            f"\n"
            f"Please rename your file to something else (e.g., '{content_type}_intro.md')\n"
            f"and update the reference in afterpython/{content_type}/myst.yml."
        )

    # Lazy import to avoid the circular dep with builders/index_md.py, which
    # already lazy-imports _write_index_file from this module.
    from afterpython.builders.index_md import _placeholder_content

    index_content = _placeholder_content(content_type)
    index_file.write_text(index_content)
    return index_file


def ensure_pnpm_11(node_env: NodeEnv) -> None:
    """Ensure pnpm 11.x is available on `node_env`'s PATH. No-op if already satisfied.

    Pinned to major 11 because an unpinned `npm install -g pnpm` previously did
    a silent 9→10 jump that broke `ap init` via ERR_PNPM_IGNORED_BUILDS. We
    pre-check the installed version so we don't redundantly invoke `npm install
    -g`, which fails with EEXIST when pnpm was installed by a different package
    manager (e.g. Homebrew) that owns the shim filenames npm wants to write.
    """
    current: str | None = None
    try:
        result = subprocess.run(
            ["pnpm", "--version"],
            env=node_env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            current = result.stdout.strip()
            if current.startswith("11."):
                return
    except FileNotFoundError:
        pass

    install = subprocess.run(
        ["npm", "install", "-g", "pnpm@11"],
        env=node_env,
        capture_output=True,
        text=True,
        check=False,
    )
    if install.returncode == 0:
        return

    msg = ["Failed to install pnpm@11 via npm."]
    if current:
        msg.append(f"Detected existing pnpm version: {current}")
    msg.append(
        "If pnpm is already installed via another package manager "
        "(e.g. Homebrew: `brew install pnpm`), npm refuses to overwrite "
        "its shims. Please either:\n"
        "  - upgrade your existing pnpm to major version 11, or\n"
        "  - uninstall it and let afterpython manage pnpm via npm."
    )
    if install.stderr:
        msg.append(f"\nnpm stderr:\n{install.stderr}")
    raise RuntimeError("\n".join(msg))


def init_myst():
    """
    Initialize MyST Markdown (mystmd) and myst.yml files in
    doc/, blog/, tutorial/, example/, guide/ directories with sensible defaults
    """
    from afterpython.const import CONTENT_TYPES
    from afterpython.utils import find_node_env

    # find any existing node.js version and use it, if no, install the Node.js version specified in NODEENV_VERSION
    node_env: NodeEnv = find_node_env()
    ensure_pnpm_11(node_env)
    for content_type in CONTENT_TYPES:
        path = ap.paths.afterpython_path / content_type
        print(f"Initializing MyST Markdown (mystmd) in {path.name}/ directory ...")
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["myst", "init"],
            cwd=path,
            input="n\n",
            text=True,
            env=node_env,
            check=True,
        )
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
    subprocess.run(["ap", "sync"])
