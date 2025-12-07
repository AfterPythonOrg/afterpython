from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

    from afterpython._typing import tContentType

import tomlkit

import afterpython as ap
from afterpython._io.toml import _to_tomlkit, read_toml, write_toml


def get_default_thumbnail(
    content_type: tContentType, file_path: Path | None = None
) -> str:
    """Get the default thumbnail value for a content type.

    Reads default thumbnail configuration from afterpython.toml:
    - Content type specific thumbnail: [website.{content_type}.thumbnail]
    - Website-wide default thumbnail: [website.thumbnail]
    - Falls back to empty string if no default is configured

    Args:
        content_type: The content type (blog, tutorial, etc.)
        file_path: Optional path to the file needing the thumbnail (for calculating relative path)

    Returns:
        The thumbnail value to use (e.g., "./static/image.png", "../static/image.png", or "")
    """
    from afterpython._io.toml import _from_tomlkit
    from afterpython.utils import get_relative_static_prefix, normalize_static_path

    afterpython = read_afterpython()
    try:
        # website_default_thumbnail = normalize_static_path(
        #     str(_from_tomlkit(afterpython.get("website", {})).get("thumbnail", ""))
        # )
        content_type_default_thumbnail = normalize_static_path(
            str(
                _from_tomlkit(afterpython.get("website", {}))
                .get(content_type, {})
                .get("thumbnail", "")
            )
        )
    except ValueError as e:
        print(f"Error in reading afterpython.toml for {content_type=}: {e}")
        return "null"

    # Determine the static prefix based on file location
    if file_path is not None:
        content_type_path = ap.paths.afterpython_path / content_type.lower()
        static_prefix = get_relative_static_prefix(file_path, content_type_path)
    else:
        static_prefix = "./"  # Default fallback

    if content_type_default_thumbnail:
        return f"{static_prefix}static{content_type_default_thumbnail}"
    # use "thumbnail" set in afterpython.toml [website]
    # elif website_default_thumbnail:
    # Website-wide static is one level up from content_type folder
    # return f"{static_prefix}../static{website_default_thumbnail}"
    else:
        return ""


def read_afterpython() -> TOMLDocument:
    """Read afterpython.toml"""
    return read_toml(ap.paths.afterpython_path / "afterpython.toml")


def update_afterpython(data_update: dict):
    """Update afterpython.toml

    Args:
        data_update: dict of data to update
    """
    from afterpython.utils import deep_merge

    afterpython_toml_path = ap.paths.afterpython_path / "afterpython.toml"

    # read existing data
    if not afterpython_toml_path.exists():
        afterpython_toml_path.touch()
        existing_data = tomlkit.document()
    else:
        with open(afterpython_toml_path, "rb") as f:
            existing_data = tomlkit.parse(f.read())
    if existing_data is None:
        existing_data = tomlkit.document()

    # convert and update existing data
    # Convert to tomlkit objects to use "array of inline tables" format
    # e.g. authors = [{name = "..."}] instead of [[docs.authors]] (array of tables)
    converted_data = _to_tomlkit(data_update)

    existing_data = deep_merge(existing_data, converted_data)

    # write updated data
    write_toml(afterpython_toml_path, existing_data)


def init_afterpython():
    """Initialize afterpython.toml"""
    afterpython_toml_path = ap.paths.afterpython_path / "afterpython.toml"
    if afterpython_toml_path.exists():
        print(f"afterpython.toml already exists at {afterpython_toml_path}")
        return
    afterpython_toml_path.touch()
    print(f"Created {afterpython_toml_path}")
    default_data = {
        "company": {
            "name": "",
            "url": "",
        },
        "website": {
            "url": "",
            "favicon": "favicon.svg",
            "logo": "logo.svg",
            "logo_dark": "logo.svg",
            "thumbnail": "thumbnail.png",
        },
    }
    update_afterpython(default_data)
