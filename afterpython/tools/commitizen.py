import afterpython as ap


commitizen_default = {
    "tool": {
        "commitizen": {
            "name": "cz_conventional_commits",
            "tag_format": "$version",
            "version_scheme": "pep440",
            "version_provider": "uv",
            "update_changelog_on_bump": False,
            "major_version_zero": True,
        }
    }
}


commitizen_pre_commit_hook = {
    "repos": [
        {
            "repo": "https://github.com/commitizen-tools/commitizen",
            "rev": "v4.10.0",
            "hooks": [
                {
                    "id": "commitizen",
                    "stages": ["commit-msg"],
                },
                {
                    "id": "commitizen-branch",
                    "stages": ["pre-push"],
                },
            ],
        },
    ]
}


def init_commitizen():
    from afterpython.tools.pre_commit import update_pre_commit
    from afterpython._io.toml import write_toml

    afterpython_path = ap.paths.afterpython_path
    commitizen_toml_path = afterpython_path / "cz.toml"
    if commitizen_toml_path.exists():
        print(f"Commitizen configuration file {commitizen_toml_path} already exists")
        return

    # Create commitizen configuration with default values
    write_toml(commitizen_toml_path, commitizen_default)
    print(f"Created {commitizen_toml_path}")

    # add commitizen hook to .pre-commit-config.yaml
    update_pre_commit(commitizen_pre_commit_hook)
