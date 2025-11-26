import shutil
import subprocess

import afterpython as ap
from afterpython._io.yaml import read_yaml, write_yaml


def install_pre_commit():
    # installed in .git/hooks
    subprocess.run(["ap", "pre-commit", "install", "--install-hooks"], check=True)


def update_pre_commit(data_update: dict):
    from afterpython.utils import deep_merge

    pre_commit_path = ap.paths.afterpython_path / ".pre-commit-config.yaml"
    if not pre_commit_path.exists():
        raise FileNotFoundError(
            f".pre-commit-config.yaml not found at {pre_commit_path}"
        )
    existing_data = read_yaml(pre_commit_path)
    existing_data = deep_merge(existing_data, data_update)
    write_yaml(pre_commit_path, existing_data)
    install_pre_commit()


def init_pre_commit():
    pre_commit_path = ap.paths.afterpython_path / ".pre-commit-config.yaml"
    if pre_commit_path.exists():
        print(f".pre-commit-config.yaml already exists at {pre_commit_path}")
        return
    pre_commit_template_path = (
        ap.paths.templates_path / "pre-commit-config-template.yaml"
    )
    shutil.copy(pre_commit_template_path, pre_commit_path)
    print(f"Created {pre_commit_path}")
    install_pre_commit()
