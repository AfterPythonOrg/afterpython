import subprocess

import pytest
from click.testing import CliRunner

from afterpython.cli.commands.init import init_content_subcommand

MYST_INIT_YML = """\
version: 1
project:
  id: test
site:
  template: book-theme
"""


@pytest.fixture
def myst_calls(monkeypatch):
    """Record the commands init_myst runs; fake `myst init` by writing a myst.yml."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd == ["myst", "init"]:
            (kwargs["cwd"] / "myst.yml").write_text(MYST_INIT_YML)
        return subprocess.CompletedProcess(cmd, returncode=0)

    monkeypatch.setattr("afterpython.tools.myst.subprocess.run", fake_run)
    monkeypatch.setattr("afterpython.utils.find_node_env", lambda: {})
    monkeypatch.setattr("afterpython.tools.myst.ensure_pnpm_12", lambda env: None)
    return calls


def test_init_content_only_creates_selected_types(project, myst_calls):
    result = CliRunner().invoke(init_content_subcommand, ["--blog", "--tutorial"])
    assert result.exit_code == 0, result.output
    created = sorted(p.name for p in project.afterpython_path.iterdir())
    assert created == ["blog", "tutorial"]
    assert myst_calls.count(["myst", "init"]) == 2
    assert myst_calls[-1] == ["ap", "sync"]


def test_init_content_all_skips_existing(project, myst_calls):
    doc = project.afterpython_path / "doc"
    doc.mkdir()
    (doc / "myst.yml").write_text("# mine\n")
    result = CliRunner().invoke(init_content_subcommand, ["--all"])
    assert result.exit_code == 0, result.output
    assert "Skipping doc/" in result.output
    assert (doc / "myst.yml").read_text() == "# mine\n"
    assert myst_calls.count(["myst", "init"]) == 4


def test_init_content_nothing_to_do_skips_sync(project, myst_calls):
    blog = project.afterpython_path / "blog"
    blog.mkdir()
    (blog / "myst.yml").write_text("")
    CliRunner().invoke(init_content_subcommand, ["--blog"])
    assert myst_calls == []


def test_init_content_requires_a_flag(project, myst_calls):
    result = CliRunner().invoke(init_content_subcommand, [])
    assert result.exit_code == 2
    assert "--all" in result.output
    assert myst_calls == []
