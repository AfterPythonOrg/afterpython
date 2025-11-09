from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv
    from pathlib import Path
    from afterpython._paths import Paths

import shutil
import subprocess

import click

from afterpython.utils.utils import find_node_env
from afterpython.builders import (
    build_metadata,
    build_blog,
    build_tutorials,
    build_examples,
    build_docs,
)


def prebuild(paths: Paths):
    def _check_initialized():
        # Check if 'ap init' has been run
        afterpython_toml = paths.afterpython_path / "afterpython.toml"
        if not afterpython_toml.exists():
            raise click.ClickException(
                "AfterPython is not initialized!\n"
                "Run 'ap init' first to set up your project."
            )

    def _clean_build_directory():
        print("Cleaning up build directory...")
        build_path = paths.build_path
        if build_path.exists():
            shutil.rmtree(build_path)
        build_path.mkdir(parents=True, exist_ok=True)

    _check_initialized()
    _clean_build_directory()


def postbuild(paths: Paths):
    def _copy_files(source: Path, destination: Path):
        if source.exists():
            for file in source.iterdir():
                if file.is_file():
                    shutil.copy2(file, destination / file.name)
                    print(f"Copied: {file.name} to {destination / file.name}")

    destination = paths.website_path / "static"
    destination.mkdir(parents=True, exist_ok=True)
    # Copy all static files from afterpython/static/ to afterpython/_website/static/
    _copy_files(paths.static_path, destination)
    # Copy all files from afterpython/_build to afterpython/_website/static/
    _copy_files(paths.build_path, destination)


@click.command()
@click.pass_context
@click.option(
    "--only-contents",
    is_flag=True,
    help="if enabled, only build contents and skip building project website",
)
def build(ctx, only_contents: bool):
    paths = ctx.obj["paths"]
    prebuild(paths)

    click.echo("Building contents...")
    build_metadata(
        pyproject_path=paths.pyproject_path,
        build_path=paths.build_path,
    )  # build metadata.json

    if not only_contents:
        click.echo("Building project website...")
        node_env: NodeEnv = find_node_env()
        subprocess.run(["pnpm", "build"], cwd=paths.website_path, env=node_env, check=True)

    postbuild(paths)
