import subprocess

import afterpython as ap
from afterpython._io.yaml import read_yaml, write_yaml

pre_commit_default = {
    # default is only ["pre-commit"], without changing the default,
    # we need to explicitly pass in --hook-type whenever we run "pre-commit install --hook-type ..."
    "default_install_hook_types": ["pre-commit", "commit-msg", "pre-push"],
    "exclude": "^afterpython/_website/",  # do not check the project website template
    "repos": [
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v6.0.0",
            "hooks": [
                {"id": "trailing-whitespace", "stages": ["pre-commit"]},
                {"id": "end-of-file-fixer", "stages": ["pre-commit"]},
                {"id": "check-yaml", "stages": ["pre-commit"]},
                {"id": "check-toml", "stages": ["pre-commit"]},
                {"id": "check-added-large-files", "stages": ["pre-commit"]},
            ],
        },
        # {
        #     "repo": "https://github.com/astral-sh/uv-pre-commit",
        #     "rev": "0.9.8",
        #     "hooks": [
        #         {"id": "uv-lock"},  # Update the uv lockfile
        #     ]
        # },
    ],
}


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
    write_yaml(pre_commit_path, pre_commit_default)
    print(f"Created {pre_commit_path}")
    install_pre_commit()
