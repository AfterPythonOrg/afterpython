from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Literal

import click

import afterpython as ap
from afterpython.tools.pyproject import read_metadata

MarimoExportMode = Literal["wasm", "static"]


def _get_molab_badge() -> str:
    return "https://marimo.io/molab-shield.svg"


def _create_molab_url(github_url: str, content_path: Path) -> str:
    """Create a molab URL for a marimo notebook at content_path (relative to afterpython/)."""
    github_url = github_url.replace("https://github.com/", "github/")
    return f"https://molab.marimo.io/{github_url}/blob/main/afterpython/{content_path.as_posix()}"


def is_marimo_notebook(path: Path) -> bool:
    """Check if a Python file is a marimo notebook.

    Looks for marimo's two reliable signature lines (`__generated_with` and
    `marimo.App(`) — both are emitted by marimo for any notebook file, and
    a plain script that just `import`s marimo won't match.
    """
    if not path.exists() or not path.is_file():
        return False
    try:
        # marimo's signature is at the top of the file, no need to read all
        head = path.read_text(encoding="utf-8", errors="ignore")[:2048]
    except OSError:
        return False
    return "__generated_with" in head and "marimo.App(" in head


def _export_marimo(source: Path, output_html: Path, mode: MarimoExportMode):
    """Run `marimo export` to produce HTML at `output_html`."""
    output_html.parent.mkdir(parents=True, exist_ok=True)
    subcommand = "html-wasm" if mode == "wasm" else "html"
    cmd = ["marimo", "export", subcommand, str(source), "-o", str(output_html)]
    # WASM-only flag: --mode edit shows code cells (interactive). Without it,
    # marimo's html-wasm subcommand defaults to "run" which hides them.
    if mode == "wasm":
        cmd += ["--mode", "edit"]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise click.ClickException(f"marimo export failed for {source}")


def _inject_molab_badge(html_path: Path, molab_url: str):
    """Insert a fixed-position molab badge near the top of the exported HTML body.

    Used so users can run the notebook on a real Python server (molab) when the
    static export can't execute, or as an alternative to the in-page WASM kernel.
    """
    if not html_path.exists():
        return
    html = html_path.read_text(encoding="utf-8")
    badge = (
        f'<a href="{molab_url}" target="_top" rel="noopener" '
        # right offset clears marimo's circular toolbar buttons in edit mode;
        # top offset is hand-tuned to vertically center against those buttons
        # (we can't group with marimo's UI, so this is a visual eyeball)
        f'style="position:fixed;top:16px;right:100px;z-index:9999;">'
        f'<img src="{_get_molab_badge()}" alt="Open in molab" />'
        f"</a>"
    )
    new_html, n = re.subn(r"(<body[^>]*>)", r"\1" + badge, html, count=1)
    if n == 0:
        click.echo(f"⚠ Could not locate <body> in {html_path}, skipping molab badge")
        return
    html_path.write_text(new_html, encoding="utf-8")


def build_marimo_notebook(
    source: Path,
    output_html: Path,
    content_path: Path,
    mode: MarimoExportMode = "wasm",
):
    """Build a single marimo notebook to HTML and inject the molab badge.

    Generic core for marimo builds — keep this notebook-agnostic so future
    callers (e.g. content-type builds in blog/tutorial) can reuse it.

    Args:
        source: Path to the marimo .py file.
        output_html: Path to write the exported HTML to.
        content_path: Path of `source` relative to afterpython/, used to build
            the molab URL (which assumes the file lives under afterpython/ on
            the user's GitHub repo).
        mode: "wasm" (interactive, Pyodide) or "static" (pre-rendered).
    """
    if not is_marimo_notebook(source):
        click.echo(f"{source} is not a marimo notebook, skip building")
        return

    click.echo(f"Building marimo notebook {source.name} (mode={mode})...")
    _export_marimo(source, output_html, mode)

    # WASM mode runs the notebook in-browser via Pyodide, so molab (a remote
    # runtime) is redundant. Skip the badge.
    if mode == "wasm":
        return

    add_molab_badge = os.getenv("AP_MOLAB_BADGE", "1") == "1"
    if not add_molab_badge:
        return

    metadata = read_metadata()
    github_url = (
        metadata.urls.get("repository") if "repository" in metadata.urls else None
    )
    if not github_url:
        click.echo(
            "⚠ Repository URL not found in [project.urls] in pyproject.toml, "
            "skipping molab badge"
        )
        return

    molab_url = _create_molab_url(github_url, content_path)
    _inject_molab_badge(output_html, molab_url)


def build_marimo_readme(mode: MarimoExportMode = "wasm"):
    """Build afterpython/README.py to _build/readme_py/readme_py.html.

    Skips silently if README.py is absent or isn't a marimo notebook so users
    who keep only README.md aren't penalized.
    """
    readme_path = ap.paths.afterpython_path / "README.py"
    if not readme_path.exists():
        return
    output_html = ap.paths.build_path / "readme_py" / "readme_py.html"
    content_path = Path("README.py")
    build_marimo_notebook(readme_path, output_html, content_path, mode)
