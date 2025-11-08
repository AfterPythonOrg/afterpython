from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import subprocess

import click

from afterpython.utils.utils import find_node_env


@click.command()
@click.pass_context
def dev(ctx):
    """Run the development server"""
    paths = ctx.obj["paths"]
    # OPTIMIZE: should implement incremental build?
    subprocess.run(["ap", "build", "--only-contents"], check=True)

    click.echo("Running the development server...")
    node_env: NodeEnv = find_node_env()
    subprocess.run(["pnpm", "dev"], cwd=paths.website_path, env=node_env, check=True)
