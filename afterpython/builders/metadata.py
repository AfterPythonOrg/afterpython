from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproject_metadata import StandardMetadata

import json

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

    print("Completed path conversion in metadata.json")


def build_metadata():
    """Build metadata.json using pyproject.toml"""
    from afterpython.tools.pyproject import read_metadata

    metadata: StandardMetadata = read_metadata()

    # Write to metadata.json
    with open(build_path / "metadata.json", "w") as f:
        json.dump(metadata.as_json(), f, indent=2)

    convert_paths()
