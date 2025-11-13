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


def update_myst_yml(data_update: dict, path: Path):
    """Update myst.yml while preserving order and formatting

    Args:
        data_update: dict of data to update
        path: path to the myst.yml file, e.g. docs/, blog/, tutorials/, examples/, guides/
    """
    from afterpython.utils.utils import deep_merge

    file_path = path / "myst.yml"

    if not file_path.exists():
        raise FileNotFoundError(
            f"myst.yml not found at {file_path}, did you forget to run `ap init` or `myst init`?"
        )

    existing_data = read_yaml(file_path) or {}
    existing_data = deep_merge(existing_data, data_update)

    # set comments for project section for convenience
      # To autogenerate a Table of Contents, run "myst init --write-toc"
    existing_data["project"].yaml_set_comment_before_after_key(
        "id",
        before="See how to create Table of Contents at: https://mystmd.org/guide/table-of-contents",
    )
    existing_data["project"].yaml_set_comment_before_after_key(
        "authors",
        before="See more authors' fields at: https://mystmd.org/guide/frontmatter#frontmatter-authors",
    )
    existing_data["project"].yaml_set_comment_before_after_key(
        "venue",
        before="See more venue's fields at: https://mystmd.org/guide/frontmatter#venue",
    )
    existing_data["site"].yaml_set_comment_before_after_key(
        "options",
        before="See options at: https://mystmd.org/guide/website-templates#site-options",
    )
    existing_data["site"].yaml_set_comment_before_after_key(
        "actions",
        before="See web layout at: https://mystmd.org/guide/website-navigation",
    )

    write_yaml(file_path, existing_data)
