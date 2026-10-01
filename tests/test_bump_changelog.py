import shutil
import subprocess

import pytest
from click.testing import CliRunner

from afterpython.cli.commands.bump import bump


def _git(project, *args):
    subprocess.run(
        ["git", *args], cwd=project.user_path, check=True, capture_output=True
    )


def _commit(project, message):
    _git(project, "commit", "--allow-empty", "-m", message)


@pytest.fixture
def repo(project):
    """A git repo at version 0.1.0 (tagged), with afterpython/cliff.toml from the template."""
    project.pyproject_path.write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\nrequires-python = ">=3.12"\n'
    )
    shutil.copy(
        project.templates_path / "cliff-template.toml",
        project.afterpython_path / "cliff.toml",
    )
    _git(project, "init", "-q", "-b", "main")
    _git(project, "config", "user.email", "test@example.com")
    _git(project, "config", "user.name", "test")
    _git(project, "add", "-A")
    _commit(project, "feat: initial")
    _git(project, "tag", "v0.1.0")
    return project


def _run_bump(*args):
    result = CliRunner().invoke(bump, list(args))
    assert result.exit_code == 0, result.output
    return result


def _committed_files(project):
    return subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=project.user_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()


def test_stable_bump_creates_changelog_in_bump_commit(repo):
    _commit(repo, "feat: add X")
    _run_bump()
    changelog = (repo.user_path / "CHANGELOG.md").read_text()
    assert "## [0.1.1]" in changelog
    assert "- Add X" in changelog
    assert "## [0.1.0]" in changelog  # a new changelog has the full history
    assert sorted(_committed_files(repo)) == ["CHANGELOG.md", "pyproject.toml"]


def test_stable_section_includes_pre_release_commits(repo):
    _commit(repo, "feat: in rc0")
    _git(repo, "tag", "v0.1.1rc0")
    _commit(repo, "fix: after rc0")
    _run_bump()
    changelog = (repo.user_path / "CHANGELOG.md").read_text()
    assert "rc0]" not in changelog
    section = changelog.split("## [0.1.0]")[0]
    assert "- In rc0" in section and "- After rc0" in section


def test_pre_release_bump_does_not_write_changelog(repo):
    _commit(repo, "feat: add X")
    _run_bump("--pre")
    assert not (repo.user_path / "CHANGELOG.md").exists()


def test_bump_prepends_and_keeps_manual_edits(repo):
    _commit(repo, "feat: add X")
    _run_bump()
    changelog_path = repo.user_path / "CHANGELOG.md"
    changelog_path.write_text(
        changelog_path.read_text().replace("- Add X", "- Add X (edited)")
    )
    _git(repo, "commit", "-am", "docs: tidy changelog")
    _commit(repo, "feat: add Y")
    _run_bump()
    changelog = changelog_path.read_text()
    assert changelog.index("## [0.1.2]") < changelog.index("## [0.1.1]")
    assert "- Add Y" in changelog
    assert "- Add X (edited)" in changelog


def test_bump_without_cliff_toml_skips_changelog(repo):
    (repo.afterpython_path / "cliff.toml").unlink()
    _git(repo, "commit", "-qam", "chore: remove cliff.toml")
    _run_bump()
    assert not (repo.user_path / "CHANGELOG.md").exists()


def test_bump_rolls_back_when_git_cliff_fails(repo):
    (repo.afterpython_path / "cliff.toml").write_text("not valid toml [")
    _git(repo, "commit", "-qam", "chore: break cliff.toml")
    result = CliRunner().invoke(bump, [])
    assert result.exit_code != 0
    assert "git-cliff failed" in result.output
    assert not (repo.user_path / "CHANGELOG.md").exists()
    assert 'version = "0.1.0"' in repo.pyproject_path.read_text()


@pytest.fixture
def interactive(monkeypatch):
    monkeypatch.setattr("afterpython.cli.commands.bump._is_interactive", lambda: True)


def test_bump_commits_changelog_edits_made_in_editor(repo, interactive, monkeypatch):
    monkeypatch.setenv("GIT_EDITOR", "sh -c 'echo edited-in-editor >> \"$0\"'")
    _commit(repo, "feat: add X")
    _run_bump()
    committed = subprocess.run(
        ["git", "show", "HEAD:CHANGELOG.md"],
        cwd=repo.user_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "edited-in-editor" in committed


def test_bump_rolls_back_when_editor_fails(repo, interactive, monkeypatch):
    monkeypatch.setenv("GIT_EDITOR", "false")
    _commit(repo, "feat: add X")
    result = CliRunner().invoke(bump, [])
    assert result.exit_code != 0
    assert "Editing failed" in result.output
    assert not (repo.user_path / "CHANGELOG.md").exists()
    assert 'version = "0.1.0"' in repo.pyproject_path.read_text()
    tags = subprocess.run(
        ["git", "tag"], cwd=repo.user_path, capture_output=True, text=True, check=True
    ).stdout.split()
    assert tags == ["v0.1.0"]


def test_bump_no_edit_skips_editor(repo, interactive, monkeypatch):
    monkeypatch.setenv("GIT_EDITOR", "false")
    _commit(repo, "feat: add X")
    _run_bump("--no-edit")
    assert "- Add X" in (repo.user_path / "CHANGELOG.md").read_text()


def test_prepended_section_includes_pre_release_commits(repo):
    _commit(repo, "feat: add X")
    _run_bump()
    _commit(repo, "feat: in rc0")
    _git(repo, "tag", "v0.1.2rc0")
    _commit(repo, "fix: after rc0")
    _run_bump()
    section = (repo.user_path / "CHANGELOG.md").read_text().split("## [0.1.1]")[0]
    assert "- In rc0" in section and "- After rc0" in section


def test_changelog_links_with_github_repo(repo, monkeypatch):
    monkeypatch.setenv("GITHUB_REPO", "owner/demo")
    _commit(repo, "feat: add X")
    _run_bump()
    _commit(repo, "fix: fix Y (#7)")
    _run_bump()
    changelog = (repo.user_path / "CHANGELOG.md").read_text()
    url = "https://github.com/owner/demo"
    assert f"## [0.1.2]({url}/compare/v0.1.1...v0.1.2)" in changelog
    assert f"- Fix Y ([#7]({url}/pull/7))" in changelog
    # sections are separated by a blank line
    assert "\n\n## [0.1.1]" in changelog


def test_changelog_has_no_links_without_github_remote(repo, monkeypatch):
    monkeypatch.delenv("GITHUB_REPO", raising=False)
    _commit(repo, "feat: add X")
    _run_bump()
    _commit(repo, "fix: fix Y (#7)")
    _run_bump()
    changelog = (repo.user_path / "CHANGELOG.md").read_text()
    assert "## [0.1.2] - " in changelog
    assert "- Fix Y (#7)" in changelog


def test_changelog_ends_with_single_newline(repo):
    _commit(repo, "feat: add X")
    _run_bump()
    _commit(repo, "feat: add Y")
    _run_bump()
    changelog = (repo.user_path / "CHANGELOG.md").read_text()
    assert changelog.endswith("\n") and not changelog.endswith("\n\n")


def test_rollback_unstages_new_changelog_changed_by_hook(repo):
    _commit(repo, "feat: add X")
    # a hook that changes the staged CHANGELOG.md and fails, like end-of-file-fixer
    hook = repo.user_path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho fixed >> CHANGELOG.md\nexit 1\n")
    hook.chmod(0o755)
    result = CliRunner().invoke(bump, [])
    assert result.exit_code != 0
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo.user_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status == ""
