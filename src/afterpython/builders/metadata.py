from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproject_metadata import StandardMetadata

import json

import click

import afterpython as ap

build_path = ap.paths.build_path


def convert_paths():
    """
    Convert paths in "description" field (README.md) in metadata.json to use the new paths in the build output.
    e.g. convert ./afterpython/static/image.png to static/image.png
    """
    # Read metadata.json
    with open(build_path / "metadata.json") as f:
        metadata = json.load(f)
        markdown_text = metadata["description"]

    # Replace with the correct paths
    updated_markdown = markdown_text.replace("afterpython/static/", "/")

    # Write back to metadata.json
    metadata["description"] = updated_markdown
    with open(build_path / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    click.echo("Completed path conversion in metadata.json")


def build_metadata():
    """Build metadata.json using pyproject.toml + afterpython.toml.

    Adds an `announcement` field (markdown string) sourced from
    `[website].announcement` in afterpython.toml, so the frontend can render
    a top-of-site banner. Empty/missing announcement → empty string.
    """
    from afterpython._io.toml import _from_tomlkit
    from afterpython.tools._afterpython import read_afterpython
    from afterpython.tools.pyproject import read_metadata

    click.echo("Building metadata.json...")

    metadata: StandardMetadata = read_metadata()
    metadata_json = metadata.as_json()

    afterpython = read_afterpython()
    website = _from_tomlkit(afterpython.get("website", {}))
    metadata_json["announcement"] = str(website.get("announcement", "")).strip()

    with open(build_path / "metadata.json", "w") as f:
        json.dump(metadata_json, f, indent=2)

    convert_paths()
