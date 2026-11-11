import json
import re
from pathlib import Path

import click
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

import afterpython as ap
from afterpython.builders.marimo_notebook import _create_molab_url, _get_molab_badge
from afterpython.const import CONTENT_TYPES
from afterpython.tools.pyproject import read_metadata


def _read_notebook(notebook_path: Path, content_path: Path) -> dict | None:
    """Read and validate a Jupyter notebook.

    Returns:
        Notebook dict if valid, None if invalid or error occurred
    """
    try:
        with open(notebook_path, encoding="utf-8") as f:
            notebook = json.load(f)
    except json.JSONDecodeError:
        click.echo(f"✗ Skipping {content_path} - invalid or empty JSON")
        return None
    except Exception as e:
        click.echo(f"✗ Error reading {content_path}: {e}")
        return None

    # Validate notebook structure
    if "cells" not in notebook:
        click.echo(f"✗ Skipping {content_path} - not a valid Jupyter notebook")
        return None

    return notebook


def _write_notebook(notebook: dict, notebook_path: Path):
    """Write a notebook dict to file."""
    # match Jupyter's own formatting (unescaped unicode, trailing newline) so
    # rewriting a committed notebook doesn't produce a noisy diff
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write("\n")


def _has_frontmatter(notebook: dict) -> bool:
    """Check if a notebook has frontmatter in the first cell."""
    if not notebook["cells"]:
        return False

    first_cell = notebook["cells"][0]
    return (
        first_cell.get("cell_type") == "markdown"
        and first_cell.get("source")
        and isinstance(first_cell["source"], list)
        and len(first_cell["source"]) > 0
        and first_cell["source"][0].strip().startswith("---")
    )


def _read_frontmatter(notebook: dict) -> str | None:
    """Read frontmatter content from a notebook.

    Returns:
        Frontmatter content as a string if it exists, None otherwise
    """
    if not _has_frontmatter(notebook):
        return None

    first_cell = notebook["cells"][0]
    return "".join(first_cell["source"])


def _write_frontmatter(notebook: dict, content: str):
    """Write frontmatter content to a notebook cell.

    Low-level function that handles cell manipulation.
    If frontmatter cell exists, updates it. If not, creates a new one.

    Args:
        notebook: The notebook dict to modify
        content: The complete frontmatter content as a string (should include --- delimiters)
    """
    # Convert content string to list of lines
    source_lines = [
        line if line.endswith("\n") else line + "\n" for line in content.split("\n")
    ]
    # Remove the last empty line if the content ends with \n
    if source_lines and source_lines[-1] == "\n":
        source_lines.pop()

    if _has_frontmatter(notebook):
        # Update existing frontmatter cell
        notebook["cells"][0]["source"] = source_lines
    else:
        # Create new frontmatter cell
        frontmatter_cell = {
            "cell_type": "markdown",
            "id": "frontmatter-cell",
            "metadata": {},
            "source": source_lines,
        }
        notebook["cells"].insert(0, frontmatter_cell)


def _add_fields_to_frontmatter(notebook: dict, fields: dict[str, str]):
    """Add or update fields in frontmatter.

    High-level function that handles frontmatter field manipulation.
    If frontmatter exists, adds new fields to it. If not, creates new frontmatter with those fields.

    Args:
        notebook: The notebook dict to modify
        fields: A dict of fields to add/update (e.g., {"thumbnail": "null"})
    """
    existing_content = _read_frontmatter(notebook)

    if existing_content:
        # Parse existing frontmatter and add new fields
        lines = existing_content.split("\n")

        # Find the closing --- of frontmatter
        closing_index = -1
        for i in range(1, len(lines)):
            if lines[i].strip().startswith("---"):
                closing_index = i
                break

        if closing_index > 0:
            # Insert new fields before the closing ---
            for key, value in fields.items():
                # Check if field already exists
                if not any(line.strip().startswith(f"{key}:") for line in lines):
                    lines.insert(closing_index, f"{key}: {value}")
                    closing_index += 1  # Adjust index for next insertion

            new_content = "\n".join(lines)
            _write_frontmatter(notebook, new_content)
    else:
        # Create new frontmatter with the provided fields
        field_lines = [f"{key}: {value}" for key, value in fields.items()]
        new_content = "---\n" + "\n".join(field_lines) + "\n---"
        _write_frontmatter(notebook, new_content)


def _add_thumbnail_to_notebook(
    notebook: dict, thumbnail: str, content_path: Path
) -> bool:
    """Add thumbnail field to a single notebook's frontmatter.

    Args:
        notebook: The notebook dict to modify
        thumbnail: The thumbnail value to add
        content_path: Path for logging purposes

    Returns:
        True if thumbnail was added, False if it already exists
    """
    # Read frontmatter content
    frontmatter_content = _read_frontmatter(notebook)

    # Check if thumbnail is already set in frontmatter
    if frontmatter_content and "thumbnail:" in frontmatter_content:
        return False

    # Add thumbnail using the fields parameter
    _add_fields_to_frontmatter(notebook, fields={"thumbnail": thumbnail})

    if frontmatter_content:
        click.echo(
            f"  ↳ Added 'thumbnail: {thumbnail}' to frontmatter in: {content_path}"
        )
    else:
        click.echo(
            f"  ↳ Created frontmatter with 'thumbnail: {thumbnail}' in: {content_path}"
        )

    return True


def _wants_molab_badge(notebook: dict) -> bool:
    """True if the notebook's frontmatter sets `molab_badge: true`, or a
    generated notebook already had it moved into its metadata."""
    if notebook.get("metadata", {}).get("afterpython", {}).get("molab_badge"):
        return True
    content = _read_frontmatter(notebook)
    if content is None:
        return False
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False
    try:
        data = YAML(typ="safe").load(match.group(1))
    except YAMLError:
        return False
    return isinstance(data, dict) and data.get("molab_badge") is True


def _remove_frontmatter_key(notebook: dict, key: str):
    content = _read_frontmatter(notebook)
    if content is None:
        return
    lines = [line for line in content.split("\n") if not line.startswith(f"{key}:")]
    _write_frontmatter(notebook, "\n".join(lines))


def _remove_molab_badge_from_notebook(notebook: dict) -> bool:
    """Remove a badge cell left by an earlier build, e.g. after `molab_badge`
    was turned off in a committed notebook. Returns True if one was removed."""
    cells = notebook["cells"]
    kept = [cell for cell in cells if cell.get("id") != "molab-badge-cell"]
    if len(kept) == len(cells):
        return False
    notebook["cells"] = kept
    return True


def _add_molab_badge_to_notebook(notebook: dict, github_url: str, content_path: Path):
    """Add a molab badge markdown cell to a single notebook.

    Args:
        notebook: The notebook dict to modify
        github_url: The GitHub repository URL
        content_path: Path relative to afterpython/ for generating the molab URL

    Note:
        The jupyter notebook needs to exist in the github repository first.
        If you have renamed a notebook, you need to push the changes to the github repository first for the badge to work.
    """
    molab_url = _create_molab_url(github_url, content_path)
    badge_md = f"[![Open in molab]({_get_molab_badge()})]({molab_url})"

    # Create a markdown cell with the badge
    badge_cell = {
        "cell_type": "markdown",
        "id": "molab-badge-cell",  # Unique ID for the badge cell
        "metadata": {
            "tags": ["molab", "hide-input"]  # Optional: use MyST tags
        },
        "source": [badge_md],
    }

    # Determine insertion position (after frontmatter if it exists)
    insert_position = 1 if _has_frontmatter(notebook) else 0

    # Check if badge already exists at the expected position
    if (
        len(notebook["cells"]) > insert_position
        and notebook["cells"][insert_position].get("id") == "molab-badge-cell"
    ):
        # Update existing badge
        notebook["cells"][insert_position] = badge_cell
        click.echo(f"✓ Updated molab badge in: {content_path}")
    else:
        # Insert at the correct position
        notebook["cells"].insert(insert_position, badge_cell)
        click.echo(f"✓ Added molab badge to: {content_path}")


def build_jupyter_notebooks():
    """Build Jupyter notebooks for all content types"""
    from afterpython.tools._afterpython import get_default_thumbnail

    # read pyproject.toml only once a notebook wants a badge
    github_url = None
    github_url_read = False

    for content_type in CONTENT_TYPES:
        click.echo(f"Building Jupyter notebooks for {content_type}/...")

        path = ap.paths.afterpython_path / content_type.lower()

        # Iterate over all .ipynb files once
        for notebook_path in path.rglob("*.ipynb"):
            # Skip MyST output and hidden tool dirs (.ipynb_checkpoints/,
            # .virtual_documents/), which aren't content
            rel_parts = notebook_path.relative_to(path).parts
            if "_build" in rel_parts or any(p.startswith(".") for p in rel_parts):
                continue

            # Get path relative to afterpython/
            content_path = notebook_path.relative_to(ap.paths.afterpython_path)

            # Get default thumbnail for this content type
            # explicitly set to "null" if no default thumbnail is set to avoid using the first image (very likely to be "open in molab" badge image) as thumbnail
            default_thumbnail = (
                get_default_thumbnail(content_type, notebook_path) or "null"
            )

            # Read the notebook
            notebook = _read_notebook(notebook_path, content_path)
            if notebook is None:
                continue

            # Track if notebook was modified
            modified = False

            # Add a molab badge if the notebook opts in with `molab_badge: true`
            # in its frontmatter. A notebook generated from a marimo .py isn't
            # committed, so the badge must open the .py instead.
            wants_badge = _wants_molab_badge(notebook)
            if wants_badge and not github_url_read:
                github_url = read_metadata().urls.get("repository")
                github_url_read = True
            if wants_badge and not github_url:
                click.echo(
                    f"⚠ Repository URL not found in [project.urls] in pyproject.toml, skipping molab badge in {content_path}"
                )
            if wants_badge and github_url:
                generated_from = (
                    notebook.get("metadata", {})
                    .get("afterpython", {})
                    .get("generated_from")
                )
                molab_path = (
                    content_path.with_name(generated_from)
                    if generated_from
                    else content_path
                )
                _add_molab_badge_to_notebook(notebook, github_url, molab_path)
                modified = True
            # MyST warns about unknown frontmatter keys. A generated notebook is
            # a build output, so move the key into its metadata, where a cached
            # rebuild still finds it; a hand-written notebook is the source and
            # must keep it.
            afterpython_metadata = notebook.get("metadata", {}).get("afterpython")
            if wants_badge and afterpython_metadata is not None:
                afterpython_metadata["molab_badge"] = True
                _remove_frontmatter_key(notebook, "molab_badge")
            elif _remove_molab_badge_from_notebook(notebook):
                modified = True

            # Add thumbnail to frontmatter
            if content_type != "doc" and _add_thumbnail_to_notebook(
                notebook, default_thumbnail, content_path
            ):
                modified = True

            # Write back if modified
            if modified:
                _write_notebook(notebook, notebook_path)
