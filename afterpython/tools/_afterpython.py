from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tomlkit.toml_document import TOMLDocument
    
import tomlkit

import afterpython as ap
from afterpython._io.toml import read_toml, write_toml, _to_tomlkit


def read_afterpython() -> TOMLDocument:
    '''Read afterpython.toml'''
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
    update_afterpython(
        {
            "company": {
                "name": "",
                "url": "",
            },
            "website": {
                "url": ""
            }
        }
    )