from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import shutil
import subprocess

import click

from afterpython.utils.utils import find_node_env


@click.command()
@click.pass_context
@click.option(
    "--no-mystmd",
    is_flag=True,
    help="if enabled, MyST Markdown will not be initialized",
)
def init(ctx, no_mystmd: bool):
    """Initialize afterpython with MyST Markdown (by default) and project website template"""
    paths = ctx.obj["paths"]
    click.echo("Initializing afterpython...")
    afterpython_path = paths.afterpython_path

    afterpython_path.mkdir(parents=True, exist_ok=True)
    paths.static_path.mkdir(parents=True, exist_ok=True)
    afterpython_path.joinpath("afterpython.toml").touch()
    # find any existing node.js version and use it, if no, install the Node.js version specified in NODEENV_VERSION
    node_env: NodeEnv = find_node_env()

    if not no_mystmd:
        click.echo(
            "Initializing MyST Markdown (mystmd) for documentation in afterpython/docs/..."
        )
        docs_path = paths.docs_path
        docs_path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["myst", "init"], cwd=docs_path, input="n\n", text=True, env=node_env
        )

    click.echo("Initializing project website template in afterpython/_website/...")
    subprocess.run(["ap", "update-website"], check=True)

    if click.confirm(
        f"\nCreate ruff.toml in {afterpython_path}?",
        default=True
    ):
        ruff_toml_path = afterpython_path / "ruff.toml"
        if ruff_toml_path.exists():
            click.echo(f"Ruff configuration file {ruff_toml_path} already exists")
            return
        ruff_template_path = afterpython_path / "ruff-template.toml"
        shutil.copy(ruff_template_path, ruff_toml_path)
        click.echo(f"Created {ruff_toml_path}")