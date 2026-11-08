"""Convert marimo notebooks in content folders into Jupyter notebooks for MyST.

MyST can't read marimo `.py` notebooks, so before MyST runs we export each one
to an `.ipynb` next to it. `marimo export ipynb --sandbox --include-outputs`
runs the notebook in its own uv environment, built from the notebook's PEP 723
header, so the outputs are reproducible no matter where `ap build` runs.

Rules
-----
- A content folder is either all-marimo or all-Jupyter (`.md` doesn't count).
  Mixing raises. Generated `.ipynb` files (stamped with
  `metadata.afterpython.generated_from`) don't count as Jupyter.
- In a marimo folder, `*.ipynb` is added to that folder's `.gitignore`: the
  `.py` is the only source, the `.ipynb` is a build artifact.
- Generated notebooks get `execute: {skip: true}` frontmatter so
  `myst build --execute` never re-runs them on the shared kernel.

Flow
----
build_marimo_content(use_cache)                   # called by prebuild()
  └─ for each content folder:
       ├─ _scan_folder()            → marimo .py / hand-written .ipynb, raises on mixing
       ├─ _remove_orphans()         → generated .ipynb whose .py is gone
       ├─ _sync_gitignore()         → add/remove the `*.ipynb` line
       └─ convert_marimo_notebook() → export + _postprocess() per notebook
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import click
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

import afterpython as ap
from afterpython.builders.jupyter_notebook import _add_fields_to_frontmatter
from afterpython.builders.marimo_notebook import is_marimo_notebook
from afterpython.const import CONTENT_TYPES

GITIGNORE_MARKER = (
    "# afterpython: .ipynb files here are generated from marimo notebooks (.py)"
)
# *.ipynb: generated notebooks; __marimo__/: marimo's session cache, which
# `marimo export` writes next to each notebook
GITIGNORE_PATTERNS = ("*.ipynb", "__marimo__/")
# re-export taking longer than this in `ap dev` prints a "too slow" hint
SLOW_EXPORT_SECONDS = 10
# nbformat cell ids: 1-64 chars of [a-zA-Z0-9-_]
_MAX_CELL_ID_LENGTH = 64


@dataclass
class _FolderScan:
    marimo: list[Path] = field(default_factory=list)
    jupyter: list[Path] = field(default_factory=list)
    generated: list[Path] = field(default_factory=list)


def _iter_files(content_path: Path):
    """Content files under a folder, skipping MyST output and hidden tool dirs
    (`.ipynb_checkpoints/`, `.virtual_documents/`), same as url_md."""
    for path in sorted(content_path.rglob("*")):
        rel_parts = path.relative_to(content_path).parts
        if "_build" in rel_parts or any(p.startswith(".") for p in rel_parts):
            continue
        if path.is_file():
            yield path


def _generated_from(notebook_path: Path) -> str | None:
    """The `.py` filename a generated notebook was exported from, else None."""
    try:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(notebook, dict):
        return None
    stamp = notebook.get("metadata", {}).get("afterpython", {})
    return stamp.get("generated_from") if isinstance(stamp, dict) else None


def _scan_folder(content_path: Path) -> _FolderScan:
    scan = _FolderScan()
    for path in _iter_files(content_path):
        if path.suffix == ".py" and is_marimo_notebook(path):
            scan.marimo.append(path)
        elif path.suffix == ".ipynb":
            if _generated_from(path):
                scan.generated.append(path)
            else:
                scan.jupyter.append(path)
    return scan


def _check_not_mixed(content_path: Path, scan: _FolderScan):
    if not (scan.marimo and scan.jupyter):
        return

    def _names(paths: list[Path]) -> str:
        return ", ".join(p.relative_to(content_path).as_posix() for p in paths)

    example = scan.jupyter[0].relative_to(content_path)
    raise click.ClickException(
        f"{content_path.name}/ mixes marimo and Jupyter notebooks:\n"
        f"    marimo:  {_names(scan.marimo)}\n"
        f"    Jupyter: {_names(scan.jupyter)}\n"
        "  A content folder must use one or the other. Convert the .ipynb "
        f"(marimo convert {example} -o {example.with_suffix('.py')}) "
        "or move it to another content folder."
    )


def _remove_orphans(scan: _FolderScan):
    """Delete generated notebooks whose marimo source no longer exists."""
    marimo = set(scan.marimo)
    for notebook_path in scan.generated:
        source = notebook_path.parent / (_generated_from(notebook_path) or "")
        if source not in marimo:
            notebook_path.unlink()
            click.echo(f"Removed {notebook_path.name} (its marimo source is gone)")


def _sync_gitignore(content_path: Path, has_marimo: bool):
    """Keep `*.ipynb` (and `__marimo__/`) in the folder's .gitignore exactly
    while it holds marimo notebooks. Only the block afterpython wrote, starting
    at GITIGNORE_MARKER, is ever added or removed."""
    gitignore = content_path / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    lines = text.splitlines()
    has_ours = GITIGNORE_MARKER in lines

    if has_marimo and not has_ours:
        existing = {line.strip() for line in lines}
        missing = [p for p in GITIGNORE_PATTERNS if p not in existing]
        if not missing:
            return  # the user already ignores these themselves
        block = "\n".join([GITIGNORE_MARKER, *missing]) + "\n"
        sep = "" if not text or text.endswith("\n") else "\n"
        gitignore.write_text(text + sep + ("\n" if text else "") + block, "utf-8")
        click.echo(
            click.style(
                f"⚠ {content_path.name}/ contains marimo notebooks: "
                f"{', '.join(missing)} added to {content_path.name}/.gitignore\n"
                "  (.ipynb files here are generated from .py and not committed)",
                fg="yellow",
            )
        )
    elif not has_marimo and has_ours:
        start = lines.index(GITIGNORE_MARKER)
        end = start + 1
        while end < len(lines) and lines[end].strip() in GITIGNORE_PATTERNS:
            end += 1
        kept = lines[:start] + lines[end:]
        while kept and not kept[-1].strip():
            kept.pop()
        gitignore.write_text("\n".join(kept) + "\n" if kept else "", "utf-8")
        click.echo(
            f"{content_path.name}/ has no marimo notebooks anymore: removed "
            f"afterpython's ignore lines from {content_path.name}/.gitignore"
        )


def _marimo_version() -> str:
    if shutil.which("marimo") is None:
        raise click.ClickException(
            "marimo is required to build marimo notebooks in content folders, "
            'install it with: uv add --dev "afterpython[marimo]"'
        )
    result = subprocess.run(
        ["marimo", "--version"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def _source_hash(source: Path) -> str:
    return hashlib.sha256(source.read_bytes()).hexdigest()


def _is_cached(source: Path, output: Path, marimo_version: str) -> bool:
    try:
        notebook = json.loads(output.read_text(encoding="utf-8"))
        stamp = notebook["metadata"]["afterpython"]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return (
        stamp.get("source_hash") == _source_hash(source)
        and stamp.get("marimo_version") == marimo_version
    )


def _as_lines(source: str | list[str]) -> list[str]:
    text = source if isinstance(source, str) else "".join(source)
    return text.splitlines(keepends=True)


def _parse_frontmatter(cell: dict) -> dict | None:
    """The YAML mapping if a markdown cell is a `---`-fenced frontmatter block."""
    if cell.get("cell_type") != "markdown":
        return None
    text = "".join(cell.get("source", [])).strip()
    match = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.DOTALL)
    if not match:
        return None
    try:
        data = YAML(typ="safe").load(match.group(1))
    except YAMLError:
        return None
    return data if isinstance(data, dict) and data else None


def _check_frontmatter_first(notebook: dict, source: Path):
    """MyST only reads frontmatter from the first cell; anywhere else it renders
    as text (the YAML becomes a garbled page title)."""
    for index, cell in enumerate(notebook["cells"]):
        if index > 0 and _parse_frontmatter(cell) is not None:
            raise click.ClickException(
                f"{source}: the frontmatter cell (--- ... ---) must be the first "
                "cell of the notebook, MyST ignores it anywhere else.\n"
                "  Move that mo.md(...) cell to the top of the file."
            )


def _project_import_name() -> str | None:
    from afterpython.tools.pyproject import read_pyproject

    # only the name is needed, so skip read_metadata()'s full validation
    try:
        name = str(read_pyproject()["project"]["name"])
    except Exception:
        return None
    return name.replace("-", "_").replace(".", "_").lower()


def _check_no_errors(notebook: dict, source: Path):
    errors = [
        output
        for cell in notebook["cells"]
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    if not errors:
        return
    first = errors[0]
    message = (
        f"{source}: {len(errors)} cell(s) raised an error while running in the "
        f"notebook's sandbox, first one:\n"
        f"    {first.get('ename')}: {first.get('evalue')}"
    )
    package = _project_import_name()
    if (
        package
        and first.get("ename") == "ModuleNotFoundError"
        and f"'{package}'" in str(first.get("evalue"))
    ):
        project_path = os.path.relpath(ap.paths.user_path, source.parent)
        message += (
            "\n  The notebook runs in its own environment, so your package must "
            "be declared in its PEP 723 header, e.g.:\n"
            "    # /// script\n"
            f'    # dependencies = ["marimo", "{package}"]\n'
            "    # [tool.uv.sources]\n"
            f'    # {package} = {{ path = "{project_path}", editable = true }}\n'
            "    # ///"
        )
    raise click.ClickException(message)


def _cell_id_prefix(source: Path, content_path: Path) -> str:
    rel = source.relative_to(content_path).with_suffix("").as_posix()
    return re.sub(r"[^A-Za-z0-9_-]", "-", rel)


def _rewrite_cell_ids(notebook: dict, prefix: str):
    """marimo derives cell ids from cell position, so every notebook repeats the
    same ids and MyST reports duplicate identifiers across the project."""
    for cell in notebook["cells"]:
        cell_id = f"{prefix}-{cell.get('id', '')}"
        if len(cell_id) > _MAX_CELL_ID_LENGTH:
            digest = hashlib.sha1(cell_id.encode()).hexdigest()[:8]
            cell_id = f"{cell_id[: _MAX_CELL_ID_LENGTH - 9]}-{digest}"
        cell["id"] = cell_id


def _postprocess(
    notebook: dict, source: Path, content_path: Path, marimo_version: str
) -> dict:
    for cell in notebook["cells"]:
        cell["source"] = _as_lines(cell.get("source", ""))
    _check_no_errors(notebook, source)
    _check_frontmatter_first(notebook, source)
    # outputs come from the sandbox, `myst build --execute` must not redo them
    _add_fields_to_frontmatter(notebook, {"execute": "{skip: true}"})
    _rewrite_cell_ids(notebook, _cell_id_prefix(source, content_path))
    notebook.setdefault("metadata", {})["afterpython"] = {
        "generated_from": source.name,
        "source_hash": _source_hash(source),
        "marimo_version": marimo_version,
    }
    return notebook


def convert_marimo_notebook(
    source: Path, content_path: Path, marimo_version: str, use_cache: bool = True
) -> bool:
    """Export one marimo notebook to `<stem>.ipynb` next to it.

    Returns True if it was (re-)exported, False if the cached output was reused.
    """
    output = source.with_suffix(".ipynb")
    if use_cache and _is_cached(source, output, marimo_version):
        return False

    click.echo(f"Running marimo notebook {source.relative_to(ap.paths.user_path)}...")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_output = Path(tmp) / output.name
        result = subprocess.run(
            [
                "marimo",
                "export",
                "ipynb",
                str(source),
                "-o",
                str(tmp_output),
                "--include-outputs",
                "--sandbox",
                # keep the author's cell order, not marimo's dependency order
                "--sort",
                "top-down",
                "--force",
            ],
            check=False,
        )
        # marimo (>=0.25) exits 1 when a cell fails but still writes the
        # notebook, so read it whenever it exists: _postprocess reports the
        # actual cell error, which is far more useful than the exit code
        if not tmp_output.exists():
            raise click.ClickException(f"marimo export failed for {source}")
        notebook = json.loads(tmp_output.read_text(encoding="utf-8"))

    notebook = _postprocess(notebook, source, content_path, marimo_version)
    if result.returncode != 0:
        raise click.ClickException(f"marimo export failed for {source}")
    output.write_text(
        json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return True


def _prepare_folder(content_path: Path) -> list[Path]:
    """Folder-level rules; returns the folder's marimo notebooks."""
    scan = _scan_folder(content_path)
    _check_not_mixed(content_path, scan)
    _remove_orphans(scan)
    _sync_gitignore(content_path, has_marimo=bool(scan.marimo))
    return scan.marimo


def build_marimo_content(use_cache: bool = True):
    """Convert every marimo notebook in the content folders to `.ipynb`.

    Args:
        use_cache: reuse a generated notebook when its `.py` and the marimo
            version are unchanged. `ap build` passes False: a notebook's
            outputs can change without its `.py` changing (e.g. it imports the
            project's own package), so production builds always re-run.
    """
    marimo_version: str | None = None
    for content_type in sorted(CONTENT_TYPES):
        content_path = ap.paths.afterpython_path / content_type
        if not content_path.exists():
            continue
        notebooks = _prepare_folder(content_path)
        if not notebooks:
            continue
        marimo_version = marimo_version or _marimo_version()
        for source in notebooks:
            convert_marimo_notebook(source, content_path, marimo_version, use_cache)


def remove_generated_notebooks(content_path: Path) -> int:
    """Delete the `.ipynb` files afterpython generated in a content folder."""
    if not content_path.exists():
        return 0
    generated = _scan_folder(content_path).generated
    for notebook_path in generated:
        notebook_path.unlink()
    return len(generated)


def watch_marimo_content(
    content_types: set[str], stop_event: threading.Event, interval: float = 1.0
):
    """`ap dev`: re-export marimo notebooks when their `.py` is saved.

    Best effort: every save re-runs the whole notebook, so errors are printed
    instead of stopping the dev servers, and slow re-runs print a hint.
    """
    content_paths = [
        ap.paths.afterpython_path / content_type
        for content_type in sorted(content_types)
    ]

    def _snapshot() -> dict[Path, float]:
        mtimes = {}
        for content_path in content_paths:
            if not content_path.exists():
                continue
            for path in content_path.rglob("*.py"):
                rel_parts = path.relative_to(content_path).parts
                if "_build" in rel_parts or any(p.startswith(".") for p in rel_parts):
                    continue
                try:
                    mtimes[path] = path.stat().st_mtime
                except OSError:
                    continue
        return mtimes

    marimo_version: str | None = None
    seen = _snapshot()
    while not stop_event.wait(interval):
        current = _snapshot()
        changed = {path for path, mtime in current.items() if seen.get(path) != mtime}
        removed = seen.keys() - current.keys()
        seen = current
        if not changed and not removed:
            continue
        for content_path in content_paths:
            if not content_path.exists():
                continue
            if not any(p.is_relative_to(content_path) for p in changed | removed):
                continue
            try:
                notebooks = _prepare_folder(content_path)
                for source in notebooks:
                    if source not in changed:
                        continue
                    marimo_version = marimo_version or _marimo_version()
                    start = time.monotonic()
                    convert_marimo_notebook(source, content_path, marimo_version)
                    elapsed = time.monotonic() - start
                    if elapsed > SLOW_EXPORT_SECONDS:
                        rel = source.relative_to(ap.paths.afterpython_path)
                        click.echo(
                            click.style(
                                f"⚠ {rel} took {elapsed:.0f}s to re-run after "
                                "saving.\n"
                                "  ap dev re-runs the whole notebook on every "
                                "save. If this is too slow, finish editing it in "
                                "`marimo edit --sandbox` first, then run ap dev.",
                                fg="yellow",
                            )
                        )
            except click.ClickException as e:
                click.echo(click.style(f"✗ {e.format_message()}", fg="red"))
            except Exception as e:  # keep watching: a crash here would go unnoticed
                click.echo(click.style(f"✗ marimo re-export failed: {e!r}", fg="red"))
