import importlib
import subprocess

import pytest

from afterpython.builders.build_pdoc import build_pdoc

# the module itself; `afterpython.builders.build_pdoc` as an attribute is the re-exported function
build_pdoc_module = importlib.import_module("afterpython.builders.build_pdoc")


@pytest.fixture
def pdoc_calls(project, monkeypatch):
    """Record the pdoc command `build_pdoc` runs instead of running it."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(build_pdoc_module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        build_pdoc_module,
        "find_package_directory",
        lambda: project.user_path / "src" / "demo",
    )
    return calls


def _write_website(project, settings: str):
    (project.afterpython_path / "afterpython.toml").write_text(
        f"[website]\n{settings}\n"
    )


def test_docformat_passed_to_pdoc(project, pdoc_calls):
    _write_website(project, 'api_reference_docformat = "google"')
    build_pdoc(base_path="")
    [cmd] = pdoc_calls
    assert cmd[cmd.index("--docformat") + 1] == "google"
    # the package stays the last argument
    assert cmd[-1] == str(project.user_path / "src" / "demo")


def test_no_docformat_by_default(project, pdoc_calls):
    _write_website(project, "api_reference = true")
    build_pdoc(base_path="")
    [cmd] = pdoc_calls
    assert "--docformat" not in cmd


def test_template_renders_dark_mode(project, tmp_path):
    """pdoc renders our template: theme script, dark colors and recolored alert icons"""
    (tmp_path / "demo.py").write_text(
        '"""Demo.\n\n> [!NOTE]\n> A note.\n"""\n\n\n'
        'def add(a: int) -> int:\n    """Add.\n\n    Args:\n        a: A number.\n    """\n'
        "    return a\n"
    )
    template_dir = project.templates_path / "pdoc"
    subprocess.run(
        [
            "pdoc",
            "--docformat",
            "google",
            "-t",
            str(template_dir),
            "-o",
            "out",
            "demo.py",
        ],
        cwd=tmp_path,
        check=True,
    )
    html = (tmp_path / "out" / "demo.html").read_text()
    assert "localStorage.getItem('theme')" in html
    assert "html.dark .pdoc{" in html  # theme.css
    assert "html.dark .pdoc-code" in html  # syntax-highlighting.css
    # custom.css: the note icon's light fill is swapped for the dark text color
    assert "fill%3D%22%236ea8fe%22" in html
    assert 'id="arguments"' in html  # google docstring sections
