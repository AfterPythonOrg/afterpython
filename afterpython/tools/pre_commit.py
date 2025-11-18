import subprocess

import afterpython as ap

from afterpython._io.yaml import write_yaml


pre_commit_default = {
    "repos": [
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v6.0.0",
            "hooks": [
                {"id": "trailing-whitespace"},
                {"id": "end-of-file-fixer"},
                {"id": "check-yaml"},
                {"id": "check-toml"},
                {"id": "check-added-large-files"},
            ]
        },
        {
            "repo": "https://github.com/astral-sh/ruff-pre-commit",
            "rev": "v0.14.5",
            "hooks": [
                # Run ruff check
                {
                    "id": "ruff-check",
                    # "args": ["--fix"],
                },  
                {"id": "ruff-format"},  # Run ruff format
            ]
        },
        # {
        #     "repo": "https://github.com/astral-sh/uv-pre-commit",
        #     "rev": "0.9.8",
        #     "hooks": [
        #         {"id": "uv-lock"},  # Update the uv lockfile
        #     ]
        # },
    ]
}


def init_pre_commit():
    pre_commit_path = ap.paths.afterpython_path / ".pre-commit-config.yaml"
    if pre_commit_path.exists():
        print(f".pre-commit-config.yaml already exists at {pre_commit_path}")
        return
    write_yaml(pre_commit_path, pre_commit_default)
    subprocess.run(["pre-commit", "install", "--config", str(pre_commit_path)], check=True)