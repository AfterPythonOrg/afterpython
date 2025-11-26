import subprocess

import click
from click.exceptions import Exit

from afterpython.utils import has_pixi, has_uv


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
def install():
    """Install all dependencies (runs 'uv sync --all-extras --all-groups' and 'pixi install' if present)"""
    if not has_uv():
        click.echo("uv not found. Please install uv first.")
        return

    result = subprocess.run(["uv", "sync", "--all-extras", "--all-groups"], check=False)
    if result.returncode != 0:
        raise Exit(result.returncode)

    if has_pixi():
        result = subprocess.run(["pixi", "install"], check=False)
        if result.returncode != 0:
            raise Exit(result.returncode)
