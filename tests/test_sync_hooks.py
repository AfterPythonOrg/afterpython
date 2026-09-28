import shutil

import pytest

from afterpython._io.yaml import read_yaml
from afterpython.tools.prek import sync_hooks


@pytest.fixture
def pre_commit_config(project):
    path = project.afterpython_path / ".pre-commit-config.yaml"
    shutil.copy(project.templates_path / "pre-commit-config-template.yaml", path)
    return path


def hook_ids(path) -> list[str]:
    return [hook["id"] for repo in read_yaml(path)["repos"] for hook in repo["hooks"]]


def add_configs(project, *names):
    for name in names:
        (project.afterpython_path / name).write_text("")


def test_all_tools_set_up_keeps_template_unchanged(project, pre_commit_config):
    add_configs(project, "ruff.toml", "ty.toml")
    before = pre_commit_config.read_text()
    sync_hooks()
    assert pre_commit_config.read_text() == before


@pytest.mark.parametrize(
    "configs, removed, kept",
    [
        (["ruff.toml"], ["ty"], ["ruff-check", "ruff-format"]),
        (["ty.toml"], ["ruff-check", "ruff-format"], ["ty"]),
        ([], ["ruff-check", "ruff-format", "ty"], []),
    ],
)
def test_removes_hooks_of_tools_not_set_up(
    project, pre_commit_config, configs, removed, kept
):
    add_configs(project, *configs)
    sync_hooks()
    ids = hook_ids(pre_commit_config)
    assert not set(removed) & set(ids)
    assert set(kept) <= set(ids)
    assert "ap-commit" in ids  # other hooks are untouched


@pytest.mark.parametrize("configs", [["ruff.toml"], ["ty.toml"], []])
def test_setting_up_later_restores_template(project, pre_commit_config, configs):
    template = pre_commit_config.read_text()
    add_configs(project, *configs)
    sync_hooks()
    # e.g. `ap init ruff` / `ap init ty` later: hooks are back where they were
    add_configs(project, "ruff.toml", "ty.toml")
    sync_hooks()
    assert pre_commit_config.read_text() == template


def test_no_pre_commit_config_is_a_no_op(project):
    sync_hooks()
    assert not (project.afterpython_path / ".pre-commit-config.yaml").exists()
