from pathlib import Path

import afterpython as ap

from ruamel.yaml import YAML


def _get_yaml() -> YAML:
    """Get configured YAML instance that preserves order, comments, and formatting"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.width = 4096  # Prevent line wrapping
    return yaml


def read_yaml(file_path: Path) -> dict:
    yaml = _get_yaml()
    with open(file_path) as f:
        return yaml.load(f)


def write_yaml(file_path: Path, data: dict):
    yaml = _get_yaml()
    with open(file_path, "w") as f:
        yaml.dump(data, f)


def read_myst_yml() -> dict:
    file_path = ap.paths.docs_path / "myst.yml"
    return read_yaml(file_path)


def update_myst_yml(data_update: dict):
    """Update myst.yml project section while preserving order and formatting

    Args:
        data_update: dict of data to update
    """
    from afterpython.utils.utils import deep_merge

    file_path = ap.paths.docs_path / "myst.yml"

    if not file_path.exists():
        raise FileNotFoundError(
            f"myst.yml not found at {file_path}, did you forget to run `ap init` or `myst init`?"
        )

    existing_data = read_yaml(file_path)
    existing_data = deep_merge(existing_data, data_update)

    existing_data["site"].yaml_set_comment_before_after_key(
        "options",
        before="See options at: https://mystmd.org/guide/website-templates#site-options",
    )
    existing_data["site"].yaml_set_comment_before_after_key(
        "actions",
        before="See web layout at: https://mystmd.org/guide/website-navigation",
    )

    write_yaml(file_path, existing_data)
