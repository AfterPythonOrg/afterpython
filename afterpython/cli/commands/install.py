import subprocess

import click
from click.exceptions import Exit

from afterpython.utils import has_uv


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
def install():
    """Run 'uv sync --all-extras --all-groups' to install all dependencies"""
    if not has_uv():
        click.echo("uv not found. Please install uv first.")
        return
    result = subprocess.run(["uv", "sync", "--all-extras", "--all-groups"], check=False)
    if result.returncode != 0:
        raise Exit(result.returncode)
