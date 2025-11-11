from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tomlkit.toml_document import TOMLDocument
    
import tomlkit

import afterpython as ap


# VIBE-CODED
def _from_tomlkit(value):
    """Recursively convert tomlkit objects to plain Python data structures.
    
    This ensures compatibility with other libraries (like ruamel.yaml):
    - tomlkit containers → plain Python containers
    - tomlkit primitives → plain Python primitives
    """
    from tomlkit.items import Array, InlineTable, Table, AoT
    
    if value is None:
        return None
    
    # Check containers first (these are the problematic ones)
    if isinstance(value, (Table, InlineTable)):
        # tomlkit dict-like → plain dict
        return {k: _from_tomlkit(v) for k, v in value.items()}
    elif isinstance(value, (Array, AoT)):
        # tomlkit array → plain list
        return [_from_tomlkit(item) for item in value]
    elif isinstance(value, dict):
        # Already a dict, but recurse to handle nested tomlkit objects
        return {k: _from_tomlkit(v) for k, v in value.items()}
    elif isinstance(value, list):
        # Already a list, but recurse to handle nested tomlkit objects
        return [_from_tomlkit(item) for item in value]
    
    # Primitives - tomlkit primitives inherit from Python types
    # Just convert explicitly to be safe
    elif isinstance(value, bool):  # MUST check bool before int!
        return bool(value)
    elif isinstance(value, int):
        return int(value)
    elif isinstance(value, float):
        return float(value)
    elif isinstance(value, str):
        return str(value)
    else:
        # datetime, date, time, or already plain Python type
        return value


# VIBE-CODED
def _to_tomlkit(value):
    """Recursively convert Python data structures to tomlkit objects.

    This ensures proper TOML formatting:
    - List of dicts → array of inline tables: [{key = val}]
    - Nested dicts → nested tables with proper structure
    """
    from tomlkit import inline_table, array
    
    if value is None:
        return None
    
    if isinstance(value, dict):
        # Plain dict → recursively convert values
        return {k: _to_tomlkit(v) for k, v in value.items()}
    elif isinstance(value, list):
        if not value:
            # Empty list → empty tomlkit array
            return array()
        
        # Check if ALL items are dicts (should be inline tables)
        if all(isinstance(item, dict) for item in value):
            arr = array()
            for item in value:
                tbl = inline_table()
                # Recursively convert the dict values
                tbl.update({k: _to_tomlkit(v) for k, v in item.items()})
                arr.append(tbl)
            return arr
        else:
            # Mixed or non-dict items → regular array
            arr = array()
            for item in value:
                arr.append(_to_tomlkit(item))
            return arr
    else:
        # Primitives (str, int, float, bool, datetime, etc.)
        # tomlkit handles these natively
        return value
    

def read_pyproject() -> TOMLDocument:
    '''Read pyproject.toml'''
    with open(ap.paths.pyproject_path, "rb") as f:
        data: TOMLDocument = tomlkit.parse(f.read())
    return data


def write_pyproject(data: TOMLDocument):
    with open(ap.paths.pyproject_path, "w") as f:
        f.write(tomlkit.dumps(data))


def read_afterpython_toml() -> TOMLDocument:
    '''Read afterpython.toml'''
    with open(ap.paths.afterpython_path / "afterpython.toml", "rb") as f:
        data: TOMLDocument = tomlkit.parse(f.read())
    return data


def update_afterpython_toml(data_update: dict):
    """Update afterpython.toml's [docs] section

    Args:
        data_update: dict of data to update
    """
    from afterpython.utils.utils import deep_merge
    afterpython_toml_path = ap.paths.afterpython_path / "afterpython.toml"

    # read existing data
    if not afterpython_toml_path.exists():
        afterpython_toml_path.touch()
        existing_data = tomlkit.document()
    else:
        with open(afterpython_toml_path, "rb") as f:
            existing_data = tomlkit.parse(f.read())

    # convert and update existing data
    # Convert to tomlkit objects to use "array of inline tables" format
    # e.g. authors = [{name = "..."}] instead of [[docs.authors]] (array of tables)
    converted_data = _to_tomlkit(data_update)

    existing_data = deep_merge(existing_data, converted_data)

    # write updated data
    with open(afterpython_toml_path, "w") as f:
        f.write(tomlkit.dumps(existing_data))