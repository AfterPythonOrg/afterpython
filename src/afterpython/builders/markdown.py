from pathlib import Path

import click

import afterpython as ap
from afterpython.const import CONTENT_TYPES


def _read_markdown(markdown_path: Path, content_path: Path) -> str | None:
    """Read and validate a markdown file.

    Args:
        markdown_path: Absolute path to the markdown file
        content_path: Path relative to afterpython/ for logging

    Returns:
        Markdown content as a string if valid, None if invalid or error occurred
    """
    try:
        with open(markdown_path, encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        click.echo(f"✗ Skipping {content_path} - file not found")
        return None
    except Exception as e:
        click.echo(f"✗ Error reading {content_path}: {e}")
        return None


def _write_markdown(content: str, markdown_path: Path):
    """Write markdown content to file.

    Args:
        content: The markdown content to write
        markdown_path: Absolute path to the markdown file
    """
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(content)


def _has_frontmatter(content: str) -> bool:
    """Check if markdown content has frontmatter.

    Args:
        content: The markdown file content as a string

    Returns:
        True if the content starts with ---, False otherwise
    """
    return content.strip().startswith("---")


def _read_frontmatter(content: str) -> str | None:
    """Read frontmatter content from markdown.

    Args:
        content: The markdown file content as a string

    Returns:
        Frontmatter content as a string (including --- delimiters) if it exists, None otherwise
    """
    if not _has_frontmatter(content):
        return None

    lines = content.split("\n")

    # Find the closing --- of frontmatter
    closing_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_index = i
            break

    if closing_index == -1:
        return None

    # Return frontmatter including both --- delimiters
    return "\n".join(lines[: closing_index + 1])


def _write_frontmatter(content: str, frontmatter: str) -> str:
    """Write frontmatter content to markdown.

    Low-level function that handles frontmatter replacement.
    If frontmatter exists in content, replaces it. If not, prepends it.

    Args:
        content: The markdown file content as a string
        frontmatter: The complete frontmatter content as a string (should include --- delimiters)

    Returns:
        The updated markdown content with the new frontmatter
    """
    if _has_frontmatter(content):
        # Replace existing frontmatter
        lines = content.split("\n")

        # Find the closing --- of existing frontmatter
        closing_index = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                closing_index = i
                break

        if closing_index > -1:
            # Remove old frontmatter and prepend new one
            body = "\n".join(lines[closing_index + 1 :])
            return frontmatter + "\n" + body
        else:
            # Malformed frontmatter, just prepend new frontmatter
            return frontmatter + "\n" + content
    else:
        # No frontmatter exists, prepend it
        return frontmatter + "\n" + content


def _ensure_blank_line_after_frontmatter(content: str) -> str:
    """Ensure there's a blank line between frontmatter and content.

    Args:
        content: The markdown content

    Returns:
        Content with blank line after frontmatter if frontmatter exists
    """
    if not _has_frontmatter(content):
        return content

    lines = content.split("\n")

    # Find the closing --- of frontmatter
    closing_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_index = i
            break

    if closing_index == -1:
        return content

    # Check if there's already a blank line after the closing ---, and if the next line is not empty, insert a blank line
    if closing_index + 1 < len(lines) and lines[closing_index + 1].strip() != "":
        lines.insert(closing_index + 1, "")

    return "\n".join(lines)


def _add_fields_to_frontmatter(content: str, fields: dict[str, str]) -> str:
    """Add or update fields in frontmatter.

    High-level function that handles frontmatter field manipulation.
    If frontmatter exists, adds new fields to it. If not, creates new frontmatter with those fields.

    Args:
        content: The markdown file content as a string
        fields: A dict of fields to add/update (e.g., {"thumbnail": "null"})

    Returns:
        The updated markdown content with the new fields in frontmatter
    """
    existing_frontmatter = _read_frontmatter(content)

    if existing_frontmatter:
        # Parse existing frontmatter and add new fields
        lines = existing_frontmatter.split("\n")

        # Find the closing --- of frontmatter
        closing_index = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                closing_index = i
                break

        if closing_index > 0:
            # Insert new fields before the closing ---
            for key, value in fields.items():
                # Check if field already exists
                if not any(line.strip().startswith(f"{key}:") for line in lines):
                    lines.insert(closing_index, f"{key}: {value}")
                    closing_index += 1  # Adjust index for next insertion

            new_frontmatter = "\n".join(lines)
            return _write_frontmatter(content, new_frontmatter)
    else:
        # Create new frontmatter with the provided fields
        field_lines = [f"{key}: {value}" for key, value in fields.items()]
        new_frontmatter = "---\n" + "\n".join(field_lines) + "\n---"
        return _write_frontmatter(content, new_frontmatter)

    return content


def _add_thumbnail_to_markdown(
    content: str, thumbnail: str, content_path: Path
) -> tuple[str, bool]:
    """Add thumbnail field to a markdown file's frontmatter.

    Args:
        content: The markdown content
        thumbnail: The thumbnail value to add
        content_path: Path for logging purposes

    Returns:
        Tuple of (modified_content, was_modified)
    """
    # Check if thumbnail is already set in frontmatter
    frontmatter_content = _read_frontmatter(content)
    if frontmatter_content and "thumbnail:" in frontmatter_content:
        return content, False

    # Add thumbnail using the fields parameter
    modified_content = _add_fields_to_frontmatter(
        content, fields={"thumbnail": thumbnail}
    )

    if frontmatter_content:
        click.echo(
            f"  ↳ Added 'thumbnail: {thumbnail}' to frontmatter in: {content_path}"
        )
    else:
        click.echo(
            f"  ↳ Created frontmatter with 'thumbnail: {thumbnail}' in: {content_path}"
        )

    return modified_content, True


def build_markdown():
    """Build markdown files for all content types"""
    from afterpython.tools._afterpython import get_default_thumbnail

    for content_type in CONTENT_TYPES:
        # Skip doc content type - docs don't need default thumbnails
        if content_type == "doc":
            continue

        click.echo(f"Building markdown files for {content_type}/...")

        path = ap.paths.afterpython_path / content_type.lower()

        # Iterate over all .md files
        for markdown_path in path.rglob("*.md"):
            # Skip files in _build directory
            if "_build" in markdown_path.parts:
                continue

            # Get path relative to afterpython/
            content_path = markdown_path.relative_to(ap.paths.afterpython_path)

            # Get default thumbnail for this content type
            default_thumbnail = get_default_thumbnail(content_type, markdown_path)

            # Read the markdown file
            content = _read_markdown(markdown_path, content_path)
            if content is None:
                continue

            # Ensure blank line after frontmatter (fixes existing files)
            original_content = content
            content = _ensure_blank_line_after_frontmatter(content)
            blank_line_added = content != original_content

            # Add thumbnail to frontmatter
            modified_content, was_modified = _add_thumbnail_to_markdown(
                content, default_thumbnail, content_path
            )

            # Write back if modified (either blank line or thumbnail)
            if was_modified or blank_line_added:
                _write_markdown(modified_content, markdown_path)
