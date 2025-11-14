from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

import afterpython as ap
from afterpython.utils import deep_merge


def _get_yaml() -> YAML:
    """Get configured YAML instance that preserves order, comments, and formatting"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.width = 4096  # Prevent line wrapping
    return yaml


def read_yaml(file_path: Path) -> CommentedMap:
    yaml = _get_yaml()
    with open(file_path) as f:
        return yaml.load(f)


def write_yaml(file_path: Path, data: dict):
    """Write YAML data"""
    yaml = _get_yaml()
    with open(file_path, "w") as f:
        yaml.dump(data, f)


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


def update_myst_yml(data_update: dict, path: Path):
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
    existing_data = deep_merge(existing_data, data_update)

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
