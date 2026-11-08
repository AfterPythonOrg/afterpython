import json
import subprocess

import click
import pytest

import afterpython.builders.marimo_content as mc

MARIMO_PY = """\
import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)
"""

FRONTMATTER = "---\ntitle: Post\ndate: 2026-11-01\n---\n\nBody.\n"


def _md(source, cell_id="Hbol"):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source}


def _code(outputs=(), cell_id="MJUe"):
    return {
        "cell_type": "code",
        "id": cell_id,
        "metadata": {},
        "source": "x = 1",
        "outputs": list(outputs),
        "execution_count": None,
    }


def _nb(*cells, metadata=None):
    return {"cells": list(cells), "metadata": metadata or {}, "nbformat": 4}


@pytest.fixture
def tutorial(project):
    path = project.afterpython_path / "tutorial"
    path.mkdir()
    (path / ".gitignore").write_text("# MyST build outputs\n_build\n")
    return path


@pytest.fixture
def fake_export(monkeypatch):
    """Fake `marimo export ipynb`: write the notebook in `exported` to `-o`."""
    exported: dict = {"nb": _nb(_md(FRONTMATTER), _code()), "returncode": 0}
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        out = cmd[cmd.index("-o") + 1]
        if exported["nb"] is not None:
            with open(out, "w") as f:
                json.dump(exported["nb"], f)
        return subprocess.CompletedProcess(cmd, returncode=int(exported["returncode"]))

    monkeypatch.setattr(mc.subprocess, "run", fake_run)
    monkeypatch.setattr(mc, "_marimo_version", lambda: "0.25.2")
    exported["calls"] = calls
    return exported


def _write_generated(path, source_name):
    path.write_text(
        json.dumps(_nb(metadata={"afterpython": {"generated_from": source_name}}))
    )


def test_mixing_marimo_and_jupyter_raises(tutorial):
    (tutorial / "a.py").write_text(MARIMO_PY)
    (tutorial / "b.ipynb").write_text(json.dumps(_nb()))
    with pytest.raises(click.ClickException, match="mixes marimo and Jupyter"):
        mc._prepare_folder(tutorial)


def test_generated_notebooks_and_plain_py_dont_count_as_mixing(tutorial):
    (tutorial / "a.py").write_text(MARIMO_PY)
    (tutorial / "helper.py").write_text("def f(): ...\n")
    _write_generated(tutorial / "a.ipynb", "a.py")
    assert mc._prepare_folder(tutorial) == [tutorial / "a.py"]


def test_md_files_dont_count_as_mixing(tutorial):
    (tutorial / "a.py").write_text(MARIMO_PY)
    (tutorial / "intro.md").write_text("# Intro\n")
    assert mc._prepare_folder(tutorial) == [tutorial / "a.py"]


def test_gitignore_added_once_and_removed_with_last_notebook(tutorial):
    gitignore = tutorial / ".gitignore"
    (tutorial / "a.py").write_text(MARIMO_PY)
    mc._prepare_folder(tutorial)
    mc._prepare_folder(tutorial)
    text = gitignore.read_text()
    assert text.count("*.ipynb") == 1
    assert "__marimo__/" in text
    assert text.startswith("# MyST build outputs\n_build\n")

    (tutorial / "a.py").unlink()
    mc._prepare_folder(tutorial)
    assert gitignore.read_text() == "# MyST build outputs\n_build\n"


def test_gitignore_untouched_when_user_already_ignores(tutorial):
    gitignore = tutorial / ".gitignore"
    gitignore.write_text("_build\n*.ipynb\n__marimo__/\n")
    (tutorial / "a.py").write_text(MARIMO_PY)
    mc._prepare_folder(tutorial)
    assert gitignore.read_text() == "_build\n*.ipynb\n__marimo__/\n"


def test_orphaned_generated_notebook_is_removed(tutorial):
    _write_generated(tutorial / "gone.ipynb", "gone.py")
    mc._prepare_folder(tutorial)
    assert not (tutorial / "gone.ipynb").exists()


def test_convert_postprocesses_and_caches(tutorial, fake_export):
    source = tutorial / "post.py"
    source.write_text(MARIMO_PY)

    assert mc.convert_marimo_notebook(source, tutorial, "0.25.2") is True
    notebook = json.loads((tutorial / "post.ipynb").read_text())
    frontmatter = "".join(notebook["cells"][0]["source"])
    assert "execute: {skip: true}" in frontmatter
    assert "title: Post" in frontmatter
    assert [c["id"] for c in notebook["cells"]] == ["post-Hbol", "post-MJUe"]
    stamp = notebook["metadata"]["afterpython"]
    assert stamp["generated_from"] == "post.py"
    assert stamp["marimo_version"] == "0.25.2"
    assert "--sandbox" in fake_export["calls"][0]

    # unchanged .py → cached; edited .py or new marimo version → re-exported
    assert mc.convert_marimo_notebook(source, tutorial, "0.25.2") is False
    assert mc.convert_marimo_notebook(source, tutorial, "0.26.0") is True
    source.write_text(MARIMO_PY + "\n# edited\n")
    assert mc.convert_marimo_notebook(source, tutorial, "0.26.0") is True
    assert (
        mc.convert_marimo_notebook(source, tutorial, "0.26.0", use_cache=False) is True
    )


def test_convert_adds_frontmatter_when_missing(tutorial, fake_export):
    fake_export["nb"] = _nb(_code())
    source = tutorial / "a.py"
    source.write_text(MARIMO_PY)
    mc.convert_marimo_notebook(source, tutorial, "0.25.2")
    notebook = json.loads((tutorial / "a.ipynb").read_text())
    assert notebook["cells"][0]["source"][1] == "execute: {skip: true}\n"
    assert notebook["cells"][0]["id"] == "a-frontmatter-cell"


def test_frontmatter_not_in_first_cell_raises(tutorial, fake_export):
    fake_export["nb"] = _nb(_code(), _md(FRONTMATTER))
    source = tutorial / "a.py"
    source.write_text(MARIMO_PY)
    with pytest.raises(click.ClickException, match="must be the first cell"):
        mc.convert_marimo_notebook(source, tutorial, "0.25.2")
    assert not (tutorial / "a.ipynb").exists()


def test_horizontal_rule_is_not_frontmatter(tutorial, fake_export):
    fake_export["nb"] = _nb(_code(), _md("---\n\nJust a divider.\n"))
    source = tutorial / "a.py"
    source.write_text(MARIMO_PY)
    assert mc.convert_marimo_notebook(source, tutorial, "0.25.2") is True


def test_cell_error_raises_with_own_package_hint(tutorial, fake_export):
    error = {
        "output_type": "error",
        "ename": "ModuleNotFoundError",
        "evalue": "No module named 'demo'",
        "traceback": [],
    }
    fake_export["nb"] = _nb(_code(outputs=[error]))
    source = tutorial / "a.py"
    source.write_text(MARIMO_PY)
    with pytest.raises(click.ClickException) as exc_info:
        mc.convert_marimo_notebook(source, tutorial, "0.25.2")
    message = exc_info.value.format_message()
    assert "ModuleNotFoundError" in message
    assert 'demo = { path = "../..", editable = true }' in message


def test_long_cell_ids_stay_valid():
    notebook = _nb(_code(cell_id="Hbol"), _code(cell_id="MJUe"))
    mc._rewrite_cell_ids(notebook, "x" * 80)
    ids = [c["id"] for c in notebook["cells"]]
    assert all(len(i) <= 64 for i in ids)
    assert len(set(ids)) == 2


def test_remove_generated_notebooks_keeps_handwritten(tutorial):
    _write_generated(tutorial / "a.ipynb", "a.py")
    (tutorial / "mine.ipynb").write_text(json.dumps(_nb()))
    assert mc.remove_generated_notebooks(tutorial) == 1
    assert sorted(p.name for p in tutorial.glob("*.ipynb")) == ["mine.ipynb"]


def test_cell_error_reported_when_marimo_exits_nonzero(tutorial, fake_export):
    # marimo >=0.25 exits 1 on a cell error but still writes the notebook
    error = {
        "output_type": "error",
        "ename": "ModuleNotFoundError",
        "evalue": "No module named 'demo'",
        "traceback": [],
    }
    fake_export["nb"] = _nb(_code(outputs=[error]))
    fake_export["returncode"] = 1
    source = tutorial / "a.py"
    source.write_text(MARIMO_PY)
    with pytest.raises(click.ClickException) as exc_info:
        mc.convert_marimo_notebook(source, tutorial, "0.25.2")
    message = exc_info.value.format_message()
    assert "No module named 'demo'" in message
    assert "tool.uv.sources" in message


@pytest.mark.parametrize("notebook", [None, _nb(_md(FRONTMATTER), _code())])
def test_nonzero_exit_without_cell_errors_fails(tutorial, fake_export, notebook):
    fake_export["nb"] = notebook
    fake_export["returncode"] = 1
    source = tutorial / "a.py"
    source.write_text(MARIMO_PY)
    with pytest.raises(click.ClickException, match="marimo export failed"):
        mc.convert_marimo_notebook(source, tutorial, "0.25.2")
    assert not (tutorial / "a.ipynb").exists()


def test_notebook_without_generated_with_is_detected(tutorial):
    (tutorial / "a.py").write_text(
        MARIMO_PY.replace('__generated_with = "0.25.2"\n', "")
    )
    assert mc._prepare_folder(tutorial) == [tutorial / "a.py"]
