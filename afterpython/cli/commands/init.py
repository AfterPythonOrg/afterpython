from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import subprocess

import click

from afterpython.const.paths import AFTERPYTHON_PATH, DOCS_PATH, STATIC_PATH
from afterpython.utils.utils import find_node_env


@click.command()
@click.option('--no-mystmd', is_flag=True, help='if enabled, MyST Markdown will not be initialized')
def init(no_mystmd: bool):
    """Initialize afterpython with MyST Markdown (by default) and project website template"""
    click.echo("Initializing afterpython...")

    AFTERPYTHON_PATH.mkdir(parents=True, exist_ok=True)
    STATIC_PATH.mkdir(parents=True, exist_ok=True)
    AFTERPYTHON_PATH.joinpath("afterpython.toml").touch()
    # find any existing node.js version and use it, if no, install the Node.js version specified in NODEENV_VERSION
    node_env: NodeEnv = find_node_env()
    
    if not no_mystmd:
        click.echo("Initializing MyST Markdown (mystmd) for documentation in afterpython/docs/...")
        DOCS_PATH.mkdir(parents=True, exist_ok=True)
        subprocess.run(["myst", "init"], cwd=DOCS_PATH, input="n\n", text=True, env=node_env)
    
    click.echo("Initializing project website template in afterpython/_website/...")
    subprocess.run(["ap", "update-template"], check=True)
