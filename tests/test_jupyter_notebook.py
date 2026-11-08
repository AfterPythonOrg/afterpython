import json

from afterpython.builders.jupyter_notebook import (
    _write_notebook,
    build_jupyter_notebooks,
)


def test_write_notebook_keeps_unicode_and_trailing_newline(tmp_path):
    path = tmp_path / "a.ipynb"
    _write_notebook({"cells": [], "metadata": {"title": "🚀 café"}}, path)
    text = path.read_text(encoding="utf-8")
    assert "🚀 café" in text
    assert text.endswith("}\n")


def test_build_skips_hidden_tool_dirs(project, monkeypatch):
    monkeypatch.setattr(
        "afterpython.tools._afterpython.get_default_thumbnail", lambda *a: None
    )
    blog = project.afterpython_path / "blog"
    (blog / ".ipynb_checkpoints").mkdir(parents=True)
    notebook = json.dumps({"cells": [], "metadata": {}})
    (blog / "post.ipynb").write_text(notebook)
    (blog / ".ipynb_checkpoints" / "post-checkpoint.ipynb").write_text(notebook)

    build_jupyter_notebooks()

    assert "thumbnail" in (blog / "post.ipynb").read_text()
    checkpoint = blog / ".ipynb_checkpoints" / "post-checkpoint.ipynb"
    assert checkpoint.read_text() == notebook


def test_failed_build_removes_placeholder_index(project, monkeypatch):
    import click
    from click.testing import CliRunner

    from afterpython.builders import create_placeholder_index_md_files
    from afterpython.cli.commands import build as build_module

    tutorial = project.afterpython_path / "tutorial"
    tutorial.mkdir()
    (tutorial / "myst.yml").write_text(
        "version: 1\nproject:\n  toc:\n  - file: post.md\n"
    )

    def failing_prebuild():
        create_placeholder_index_md_files()
        raise click.ClickException("a marimo notebook failed")

    monkeypatch.setattr(build_module, "prebuild", failing_prebuild)
    monkeypatch.setattr("afterpython.utils.is_website_initialized", lambda: True)

    result = CliRunner().invoke(build_module.build, [], obj={"paths": project})

    assert result.exit_code != 0
    assert "a marimo notebook failed" in result.output
    assert not (tutorial / "index.md").exists()
    assert "index.md" not in (tutorial / "myst.yml").read_text()
