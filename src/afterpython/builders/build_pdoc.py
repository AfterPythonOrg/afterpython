import os
import subprocess

import click

import afterpython as ap
from afterpython.tools.pyproject import find_package_directory


def build_pdoc(base_path: str) -> None:
    """Generate API reference HTML from the user's package via pdoc.

    Output goes to `_build/api_reference/` (the standard staging dir);
    the build command is responsible for copying it into the website's
    static dir.

    `base_path` is "" for custom domains and "/{repo-name}" for GitHub
    Pages — used to wire pdoc's logo + logo-link flags so that the
    project logo appears in the top-left of every API page and links
    back to the project website root (matches MyST's UX).
    """
    package_dir = find_package_directory()
    output_dir = ap.paths.build_path / "api_reference"
    template_dir = ap.paths.templates_path / "pdoc"

    click.echo("Building api_reference/...")

    # PDOC_ALLOW_EXEC=1 lets module-level subprocess calls run during pdoc's
    # introspection import. Required because some deps (e.g. jupytext) shell
    # out to `pandoc --version` at import time. Safe here: pdoc imports the
    # user's own package, whose import-time behavior the user already trusts.
    env = {**os.environ, "PDOC_ALLOW_EXEC": "1"}

    # logo.svg is a project-website-template convention (always present in
    # `_website/static/`); served at `{base_path}/logo.svg` once the site
    # is built. logo-link points back to the project website root.
    result = subprocess.run(
        [
            "pdoc",
            "-o",
            str(output_dir),
            "--logo",
            f"{base_path}/logo.svg",
            "--logo-link",
            f"{base_path}/",
            "--template-directory",
            str(template_dir),
            str(package_dir),
        ],
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise click.ClickException(
            f"pdoc failed with exit code {result.returncode}. "
            f"Re-run `ap build --skip-api` to skip API reference generation."
        )
