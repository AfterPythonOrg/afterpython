import subprocess

import click

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
    subprocess.run(["uv", "sync", "--all-extras", "--all-groups"], check=True)
