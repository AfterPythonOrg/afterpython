from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import tContentType

import json
from pathlib import Path

from pyproject_metadata import StandardMetadata

import afterpython as ap
from afterpython.const import CONTENT_TYPES
from afterpython.tools.pyproject import read_metadata


def _get_molab_badge() -> str:
    return "https://marimo.io/molab-shield.svg"


def _create_molab_url(github_url: str, content_path: Path):
    """Create a molab URL for a given content type and notebook path.
    Args:
        github_url: str, e.g. "https://github.com/AfterPythonOrg/afterpython"
        content_path: str, e.g. "tutorial/test.ipynb"
    """
    github_url = github_url.replace("https://github.com/", "github/")
    return f"https://molab.marimo.io/{github_url}/blob/main/afterpython/{content_path.as_posix()}"


def add_molab_badge_to_jupyter_notebooks(content_type: tContentType):
    """Add a badge markdown cell to the top of Jupyter notebooks in the given content type directory, e.g. tutorial/, blog/, etc.
    # NOTE
    Note that the jupyter notebooks need to exist in the github repository first.
    If you have renamed a notebook, you need to push the changes to the github repository first for the badge to work.
    """
    assert content_type.lower() in CONTENT_TYPES, (
        f"Invalid content type: {content_type}"
    )
    metadata: StandardMetadata = read_metadata()

    if "repository" not in metadata.urls:
        return "Repository URL not found in [project.urls] in pyproject.toml, cannot add molab badge"
    else:
        github_url = metadata.urls["repository"]

    path = ap.paths.afterpython_path / content_type.lower()

    # iterate over all files in the path
    for notebook_path in path.rglob("*.ipynb"):
        # Skip files in _build directory
        if "_build" in notebook_path.parts:
            continue

        # Get path relative to afterpython/ (includes tutorial/ in the path)
        content_path = notebook_path.relative_to(ap.paths.afterpython_path)
        molab_url = _create_molab_url(github_url, content_path)
        badge_md = f"[![Open in molab]({_get_molab_badge()})]({molab_url})"

        # Read the notebook
        try:
            # Read the notebook
            with open(notebook_path) as f:
                notebook = json.load(f)
        except json.JSONDecodeError:
            print(f"✗ Skipping {content_path} - invalid or empty JSON")
            continue
        except Exception as e:
            print(f"✗ Error reading {content_path}: {e}")
            continue

        # Validate notebook structure
        if "cells" not in notebook:
            print(f"✗ Skipping {content_path} - not a valid Jupyter notebook")
            continue

        # Create a markdown cell with the badge
        badge_cell = {
            "cell_type": "markdown",
            "id": "molab-badge-cell",  # Unique ID for the badge cell
            "metadata": {
                "tags": ["molab", "hide-input"]  # Optional: use MyST tags
            },
            "source": [badge_md],
        }

        # Check if first cell is already a badge cell (avoid duplicates)
        if notebook["cells"] and notebook["cells"][0].get("id") == "molab-badge-cell":
            # Update existing badge
            notebook["cells"][0] = badge_cell
            print(f"✓ Updated molab badge in: {content_path}")
        else:
            # Insert at the beginning
            notebook["cells"].insert(0, badge_cell)
            print(f"✓ Added molab badge to: {content_path}")

        # Write back
        with open(notebook_path, "w") as f:
            json.dump(notebook, f, indent=1)
