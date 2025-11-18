import subprocess

import click

import afterpython as ap

from afterpython.utils import has_uv


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.option('--pre-commit', is_flag=True, help='run "pre-commit install --all-files"')
def install(pre_commit: bool):
    """Run 'uv sync --all-extras --all-groups' to install all dependencies"""
    if not has_uv():
        click.echo("uv not found. Please install uv first.")
        return
    subprocess.run(["uv", "sync", "--all-extras", "--all-groups"], check=True)
    if pre_commit:
        pre_commit_path = ap.paths.afterpython_path / ".pre-commit-config.yaml"
        subprocess.run(["pre-commit", "install", "--config", str(pre_commit_path)], check=True)