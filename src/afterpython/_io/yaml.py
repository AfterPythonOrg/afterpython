from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


def _get_yaml() -> YAML:
    """Get configured YAML instance that preserves order, comments, and formatting"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.width = 4096  # Prevent line wrapping
    return yaml


def read_yaml(file_path: Path) -> CommentedMap:
    yaml = _get_yaml()
    with open(file_path) as f:
        return yaml.load(f)


def write_yaml(file_path: Path, data: dict):
    """Write YAML data"""
    yaml = _get_yaml()
    with open(file_path, "w") as f:
        yaml.dump(data, f)
