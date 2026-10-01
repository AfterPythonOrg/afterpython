import pytest
from click.testing import CliRunner

from afterpython.cli.commands.bump import PRE_RELEASE_TAGS
from afterpython.cli.commands.changelog import changelog
from afterpython.cli.commands.init import init_cliff


def test_init_cliff_creates_config_from_template(project):
    init_cliff()
    cliff_toml = project.afterpython_path / "cliff.toml"
    template = project.templates_path / "cliff-template.toml"
    assert cliff_toml.read_text() == template.read_text()


def test_init_cliff_keeps_existing_config(project):
    cliff_toml = project.afterpython_path / "cliff.toml"
    cliff_toml.write_text("# my settings\n")
    init_cliff()
    assert cliff_toml.read_text() == "# my settings\n"


@pytest.mark.parametrize("conflict", ["cliff.toml", "[tool.git-cliff]"])
def test_init_cliff_skips_on_existing_cliff_config(project, conflict, capsys):
    if conflict == "cliff.toml":
        (project.user_path / "cliff.toml").write_text("")
    else:
        with open(project.pyproject_path, "a") as f:
            f.write("\n[tool.git-cliff]\n")
    init_cliff()
    assert not (project.afterpython_path / "cliff.toml").exists()
    assert "Skipped git-cliff setup" in capsys.readouterr().out


@pytest.fixture
def cliff_calls(monkeypatch):
    """Record the commands `ap changelog` runs instead of running git-cliff."""
    import subprocess

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0)

    monkeypatch.setattr("afterpython.cli.commands.changelog.subprocess.run", fake_run)
    return calls


def test_changelog_previews_unreleased_by_default(project, cliff_calls):
    (project.afterpython_path / "cliff.toml").write_text("")
    result = CliRunner().invoke(changelog, [])
    assert result.exit_code == 0, result.output
    assert cliff_calls == [
        [
            "git-cliff",
            "--config",
            str(project.afterpython_path / "cliff.toml"),
            "--ignore-tags",
            PRE_RELEASE_TAGS,
            "--unreleased",
        ]
    ]


def test_changelog_passes_args_to_git_cliff(project, cliff_calls):
    (project.afterpython_path / "cliff.toml").write_text("")
    result = CliRunner().invoke(changelog, ["--ignore-tags", "rc", "--latest"])
    assert result.exit_code == 0, result.output
    assert cliff_calls == [
        [
            "git-cliff",
            "--config",
            str(project.afterpython_path / "cliff.toml"),
            "--ignore-tags",
            "rc",
            "--latest",
        ]
    ]


def test_changelog_without_cliff_toml_fails(project, cliff_calls):
    result = CliRunner().invoke(changelog, [])
    assert result.exit_code != 0
    assert "ap init cliff" in result.output
    assert cliff_calls == []
