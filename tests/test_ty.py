import pytest
from click.testing import CliRunner

from afterpython.cli.commands.check import check
from afterpython.cli.commands.init import init_ty


def test_init_ty_creates_config_from_template(project):
    init_ty()
    ty_toml = project.afterpython_path / "ty.toml"
    template = project.templates_path / "ty-template.toml"
    assert ty_toml.read_text() == template.read_text()


def test_init_ty_keeps_existing_config(project):
    ty_toml = project.afterpython_path / "ty.toml"
    ty_toml.write_text("# my settings\n")
    init_ty()
    assert ty_toml.read_text() == "# my settings\n"


@pytest.mark.parametrize("conflict", ["ty.toml", "[tool.ty]"])
def test_init_ty_skips_on_existing_ty_config(project, conflict, capsys):
    if conflict == "ty.toml":
        (project.user_path / "ty.toml").write_text("")
    else:
        with open(project.pyproject_path, "a") as f:
            f.write("\n[tool.ty]\n")
    init_ty()
    assert not (project.afterpython_path / "ty.toml").exists()
    assert "Skipped ty setup" in capsys.readouterr().out


@pytest.fixture
def ty_calls(monkeypatch):
    """Record the commands `ap check` runs instead of running ty."""
    import subprocess

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0)

    monkeypatch.setattr("afterpython.cli.commands.check.subprocess.run", fake_run)
    return calls


def test_check_uses_afterpython_ty_toml(project, ty_calls):
    (project.afterpython_path / "ty.toml").write_text("")
    result = CliRunner().invoke(check, ["src/", "--output-format", "concise"])
    assert result.exit_code == 0, result.output
    assert ty_calls == [
        [
            "ty",
            "check",
            "--project",
            str(project.user_path),
            "--config-file",
            str(project.afterpython_path / "ty.toml"),
            "src/",
            "--output-format",
            "concise",
        ]
    ]


def test_check_without_ty_toml_lets_ty_find_its_config(project, ty_calls):
    result = CliRunner().invoke(check, [])
    assert result.exit_code == 0, result.output
    assert ty_calls == [["ty", "check", "--project", str(project.user_path)]]


def test_check_passes_on_ty_exit_code(project, monkeypatch):
    import subprocess

    monkeypatch.setattr(
        "afterpython.cli.commands.check.subprocess.run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, returncode=1),
    )
    assert CliRunner().invoke(check, []).exit_code == 1
