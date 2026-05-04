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

    Adds two frontend-only fields sourced from `[website]` in afterpython.toml:
    - `announcement`: markdown banner string (empty when unset)
    - `readme_py`: "wasm" | "static" | "" — resolved to "" when README.py is
      missing or isn't a marimo notebook, so the frontend can use a single
      truthiness check to decide between iframe and markdown description.
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
    metadata_json["readme_py"] = _resolve_readme_py(website)

    with open(build_path / "metadata.json", "w") as f:
        json.dump(metadata_json, f, indent=2)

    convert_paths()


def _resolve_readme_py(website_config: dict) -> str:
    """Resolve the readme_py field for metadata.json.

    Returns "wasm" | "static" only when afterpython/README.py exists AND is a
    marimo notebook, so the toml setting is honored only when there's actually
    something to render. Otherwise returns "".
    """
    from afterpython.builders.marimo_notebook import is_marimo_notebook

    readme_path = ap.paths.afterpython_path / "README.py"
    if not is_marimo_notebook(readme_path):
        return ""

    mode = str(website_config.get("readme_py", "wasm"))
    if mode not in ("wasm", "static"):
        return "wasm"
    return mode
