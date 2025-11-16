from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv
    from pathlib import Path

import os
import shutil
import subprocess

import click

import afterpython as ap
from afterpython.utils import find_node_env
from afterpython.const import CONTENT_TYPES
from afterpython.builders import (
    build_metadata,
    add_molab_badge_to_jupyter_notebooks,
)


def prebuild():
    def _check_initialized():
        # Check if 'ap init' has been run
        afterpython_toml = ap.paths.afterpython_path / "afterpython.toml"
        if not afterpython_toml.exists():
            raise click.ClickException(
                "AfterPython is not initialized!\n"
                "Run 'ap init' first to set up your project."
            )

    def _clean_build_directory():
        print("Cleaning up build directory...")
        build_path = ap.paths.build_path
        if build_path.exists():
            shutil.rmtree(build_path)
        build_path.mkdir(parents=True, exist_ok=True)

    _check_initialized()
    _clean_build_directory()
    
    if os.getenv("AP_MOLAB_BADGE", "0") == "1":
        for content_type in CONTENT_TYPES:
            add_molab_badge_to_jupyter_notebooks(content_type)


def postbuild():
    def _copy_files(source: Path, destination: Path):
        if source.exists():
            for file in source.iterdir():
                if file.is_file():
                    shutil.copy2(file, destination / file.name)
                    print(f"Copied: {file.name} to {destination / file.name}")

    destination = ap.paths.website_path / "static"
    destination.mkdir(parents=True, exist_ok=True)
    # Copy all static files from afterpython/static/ to afterpython/_website/static/
    _copy_files(ap.paths.static_path, destination)
    # Copy all files from afterpython/_build to afterpython/_website/static/
    _copy_files(ap.paths.build_path, destination)


@click.command()
@click.pass_context
@click.option(
    "--only-contents",
    is_flag=True,
    help="if enabled, only build contents and skip building project website",
)
def build(ctx, only_contents: bool):
    paths = ctx.obj["paths"]
    prebuild()

    click.echo("Building contents...")
    build_metadata()  # build metadata.json

    if not only_contents:
        click.echo("Building project website...")
        node_env: NodeEnv = find_node_env()
        subprocess.run(["pnpm", "build"], cwd=paths.website_path, env=node_env, check=True)

    postbuild()
