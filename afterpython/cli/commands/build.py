from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import shutil
import subprocess

import click

from afterpython.utils.utils import find_node_env
from afterpython.const.paths import AFTERPYTHON_PATH, WEBSITE_PATH, BUILD_PATH
from afterpython.builders import (
    build_metadata,
    build_blog,
    build_tutorials,
    build_examples,
    build_docs,
)


def prebuild():
    BUILD_PATH.mkdir(parents=True, exist_ok=True)
    def _check_initialized():
        # Check if 'ap init' has been run
        config_file = AFTERPYTHON_PATH / "afterpython.toml"
        if not config_file.exists():
            raise click.ClickException(
                "AfterPython is not initialized!\n"
                "Run 'ap init' first to set up your project."
            )
    _check_initialized()


def postbuild():
    destination = WEBSITE_PATH / 'static'
    destination.mkdir(parents=True, exist_ok=True)
    def _copy_static_files():
        # Copy all static files from afterpython/static/ to afterpython/_website/static/
        source_static = AFTERPYTHON_PATH / 'static'
        if source_static.exists():
            for file in source_static.iterdir():
                if file.is_file():
                    shutil.copy2(file, destination / file.name)
                    print(f"Copied: {file.name} to {destination / file.name}")
    def _copy_build_files():
        # Copy all files from afterpython/_build to afterpython/_website/static/
        source_build = BUILD_PATH
        if source_build.exists():
            for file in source_build.iterdir():
                if file.is_file():
                    shutil.copy2(file, destination / file.name)
                    print(f"Copied: {file.name} to {destination / file.name}")
    _copy_static_files()       
    _copy_build_files()


@click.command()
@click.option('--only-contents', is_flag=True, help='if enabled, only build contents and skip building project website')
def build(only_contents: bool):
    prebuild()
    
    click.echo("Building contents...")
    build_metadata()  # build metadata.json

    if not only_contents:
        click.echo("Building project website...")
        node_env: NodeEnv = find_node_env()
        subprocess.run(["pnpm", "build"], cwd=WEBSITE_PATH, env=node_env, check=True)

    postbuild()