import subprocess

import click
from click.exceptions import Exit

from afterpython.utils import has_pixi, has_uv


@click.command()
def lock():
    """Lock the dependencies (runs 'uv lock' and 'pixi lock' if present)"""
    if not has_uv():
        click.echo("uv not found. Please install uv first.")
        return

    result = subprocess.run(["uv", "lock"], check=False)
    if result.returncode != 0:
        raise Exit(result.returncode)

    if has_pixi():
        result = subprocess.run(["pixi", "lock"], check=False)
        if result.returncode != 0:
            raise Exit(result.returncode)
