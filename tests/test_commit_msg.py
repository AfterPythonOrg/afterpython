import pytest
from click.testing import CliRunner

from afterpython.cli.commands.commit_msg import commit_msg

COMMIT_TYPES = {"feat": "A new feature", "fix": "A bug fix", "wip": "Work in progress"}


@pytest.fixture(autouse=True)
def fake_afterpython_toml(monkeypatch):
    import tomlkit

    doc = tomlkit.parse(tomlkit.dumps({"commit": {"types": COMMIT_TYPES}}))
    monkeypatch.setattr("afterpython.tools._afterpython.read_afterpython", lambda: doc)


def run(tmp_path, message: str):
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text(message, encoding="utf-8")
    return CliRunner().invoke(commit_msg, [str(msg_file)])


@pytest.mark.parametrize(
    "message",
    [
        "feat: add X",
        "fix(cli): handle Y",
        "feat!: drop Z",
        "feat(api)!: drop Z",
        "wip: custom type from config",
        "feat: subject\n\nA longer body\nover several lines",
        # comments written by git's template/editor are ignored
        "# Please enter the commit message\n\nfix: after comments",
        # git-generated messages
        "Merge branch 'dev' into main",
        'Revert "feat: add X"',
        "fixup! feat: add X",
        "squash! feat: add X",
        "amend! feat: add X",
        # empty message: git rejects it itself
        "",
        "# only comments\n",
    ],
)
def test_accepted(tmp_path, message):
    result = run(tmp_path, message)
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    "message, reason",
    [
        ("chore: not in config", "unknown commit type 'chore'"),
        ("docs: not in config", "unknown commit type 'docs'"),
        ("add X", "doesn't follow the format"),
        ("feat:missing space", "doesn't follow the format"),
        ("feat: ", "doesn't follow the format"),
        ("Feat: uppercase type", "doesn't follow the format"),
        # the diff shown by `git commit -v` is not part of the message
        (
            "bad message\n# ------------------------ >8 ------------------------\nfeat: x",
            "doesn't follow the format",
        ),
    ],
)
def test_rejected(tmp_path, message, reason):
    result = run(tmp_path, message)
    assert result.exit_code == 1
    assert reason in result.output
    assert "SKIP=ap-commit git commit" in result.output


def test_error_lists_allowed_types(tmp_path):
    result = run(tmp_path, "nope")
    for t, desc in COMMIT_TYPES.items():
        assert t in result.output and desc in result.output


@pytest.mark.parametrize("toml", ["", "[commit.types]\n"])
def test_no_commit_types_skips_check(tmp_path, monkeypatch, toml):
    import tomlkit

    monkeypatch.setattr(
        "afterpython.tools._afterpython.read_afterpython",
        lambda: tomlkit.parse(toml),
    )
    result = run(tmp_path, "anything goes")
    assert result.exit_code == 0, result.output
    assert result.output == ""


GIT_DEFAULT_MESSAGE = (
    "\n# Please enter the commit message for your changes. Lines starting\n"
    "# with '#' will be ignored, and an empty message aborts the commit.\n"
)


def run_template(tmp_path, message: str, source: str | None = None):
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text(message, encoding="utf-8")
    env = {"PRE_COMMIT_COMMIT_MSG_SOURCE": source} if source else {}
    result = CliRunner().invoke(commit_msg, [str(msg_file), "--template"], env=env)
    return result, msg_file.read_text(encoding="utf-8")


def test_template_added_for_plain_commit(tmp_path):
    result, text = run_template(tmp_path, GIT_DEFAULT_MESSAGE)
    assert result.exit_code == 0, result.output
    lines = text.splitlines()
    # subject line stays empty, template comes before git's own comments
    assert lines[0] == ""
    assert all(line.startswith("#") for line in lines[1:])
    for t, desc in COMMIT_TYPES.items():
        assert any(t in line and desc in line for line in lines)
    assert text.index("[commit.types]") < text.index("Please enter the commit message")
    assert "SKIP=ap-commit" in text


def test_template_keeps_user_template_text(tmp_path):
    # e.g. text coming from git's own commit.template
    result, text = run_template(tmp_path, "feat: \n" + GIT_DEFAULT_MESSAGE, "template")
    assert result.exit_code == 0, result.output
    assert text.startswith("feat: \n\n# Format:")


@pytest.mark.parametrize("source", ["message", "merge", "squash", "commit"])
def test_template_skipped_when_message_given(tmp_path, source):
    original = "feat: from -m\n"
    result, text = run_template(tmp_path, original, source)
    assert result.exit_code == 0, result.output
    assert text == original


def test_template_never_breaks_the_check(tmp_path):
    # the template itself is all comments, so an untouched template is an empty message
    _, text = run_template(tmp_path, GIT_DEFAULT_MESSAGE)
    assert run(tmp_path, text).exit_code == 0
    assert run(tmp_path, "feat: add X\n" + text.lstrip("\n")).exit_code == 0
