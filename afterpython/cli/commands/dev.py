from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import click
import subprocess

from afterpython.utils.utils import find_node_env
from afterpython.const.paths import WEBSITE_PATH


@click.command()
def dev():
    """Run the development server"""
    click.echo("Running the development server...")
    node_env: NodeEnv = find_node_env()
    subprocess.run(["pnpm", "dev"], cwd=WEBSITE_PATH, env=node_env, check=True)