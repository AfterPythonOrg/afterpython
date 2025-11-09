import json
import tomllib
from pathlib import Path

from pyproject_metadata import StandardMetadata


def convert_paths(build_path: Path):
    """
    Convert paths in "description" field (README.md) in metadata.json to use the new paths in the build output.
    e.g. convert ./afterpython/static/image.png to static/image.png
    """
    # Read metadata.json
    with open(build_path / "metadata.json") as f:
        metadata = json.load(f)
        markdown_text = metadata["description"]

    # Replace with the correct paths
    updated_markdown = markdown_text.replace("./afterpython/static/", "/")

    # Write back to metadata.json
    metadata["description"] = updated_markdown
    with open(build_path / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("Completed path conversion in metadata.json")


def build_metadata(pyproject_path: Path, build_path: Path):
    """Build metadata.json using pyproject.toml"""
    # Read and parse pyproject.toml
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Create metadata object
    metadata = StandardMetadata.from_pyproject(pyproject_data)

    # Write to metadata.json
    with open(build_path / "metadata.json", "w") as f:
        json.dump(metadata.as_json(), f, indent=2)

    convert_paths(build_path)
