import shutil

import afterpython as ap


def init_commitizen():
    commitizen_toml_path = ap.paths.afterpython_path / "cz.toml"
    if commitizen_toml_path.exists():
        print(f"Commitizen configuration file {commitizen_toml_path} already exists")
        return
    cz_template_path = ap.paths.templates_path / "cz-template.toml"
    shutil.copy(cz_template_path, commitizen_toml_path)
    print(f"Created {commitizen_toml_path}")
