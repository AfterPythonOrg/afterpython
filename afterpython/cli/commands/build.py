from __future__ import annotations
from typing import TYPE_CHECKING
from collections.abc import Callable

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv
    from pathlib import Path

import os
import shutil
import subprocess

import click
from click.exceptions import Exit

import afterpython as ap
from afterpython.utils import find_node_env
from afterpython.const import CONTENT_TYPES
from afterpython.builders import (
    build_metadata,
    add_molab_badge_to_jupyter_notebooks,
)


def determine_base_path() -> str:
    """Determine BASE_PATH based on website URL configuration.

    Returns:
        Empty string if custom domain is configured (no github.io in URL)
        /repo-name if using default GitHub Pages URL (contains github.io)
    """
    from afterpython.tools._afterpython import read_afterpython
    from afterpython.tools.pyproject import read_metadata
    from afterpython._io.toml import _from_tomlkit

    # Read website URL from afterpython.toml
    afterpython = read_afterpython()
    website_url = str(_from_tomlkit(afterpython["website"]).get("url", ""))

    # If custom domain (no github.io), no BASE_PATH needed
    if "github.io" not in website_url:
        return ""

    # For GitHub Pages default URL, extract repo name from repository URL
    pyproject = read_metadata()
    github_url = str(pyproject.urls.get("repository", ""))

    if not github_url:
        click.echo(
            "Warning: No repository URL found in pyproject.toml, using empty BASE_PATH"
        )
        return ""

    # Extract repo name from URL like "https://github.com/AfterPythonOrg/afterpython"
    # -> "afterpython"
    repo_name = github_url.rstrip("/").split("/")[-1]
    return f"/{repo_name}"


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

    if os.getenv("AP_MOLAB_BADGE", "1") == "1":
        for content_type in CONTENT_TYPES:
            add_molab_badge_to_jupyter_notebooks(content_type)


def postbuild():
    def _move_files(
        source: Path,
        destination: Path,
        is_copy: bool = True,
        ignore_copy: Callable[[str, list[str]], set[str]] | None = None,
    ):
        """
        Move or copy files from source to destination.

        Args:
            source: Source path
            destination: Destination path
            is_copy: If True, copy files (merge with existing). If False, move files (replace destination)
            ignore_copy: Optional ignore function for copytree, takes (directory, contents) and returns set of names to ignore
        """
        if not source.exists():
            return
        if is_copy:
            shutil.copytree(source, destination, dirs_exist_ok=True, ignore=ignore_copy)
            print(f"Copied: {source} to {destination}")
        else:
            # Remove destination if it exists (move will fail otherwise)
            if destination.exists():
                shutil.rmtree(destination)
            shutil.move(str(source), str(destination))
            print(f"Moved: {source} to {destination}")

    website_static = ap.paths.website_path / "static"
    website_static.mkdir(parents=True, exist_ok=True)

    for content_type in CONTENT_TYPES:
        myst_build = ap.paths.afterpython_path / content_type / "_build"
        afterpython_content_build = ap.paths.build_path / content_type
        # Move myst builds from afterpython/{content_type}/_build to afterpython/_build/{content_type}
        _move_files(myst_build, afterpython_content_build, is_copy=False)
        # Copy afterpython/_build/{content_type}/html to afterpython/_website/static/{content_type}
        _move_files(
            afterpython_content_build / "html",
            website_static / content_type,
            is_copy=True,
        )

    # Copy all files from afterpython/_build to afterpython/_website/static/
    _move_files(
        ap.paths.build_path,
        website_static,
        is_copy=True,
        # ignore all content builds e.g. doc/, blog/, only their html/ files will be copied
        ignore_copy=lambda dir, contents: [
            name for name in contents if name in CONTENT_TYPES
        ],
    )

    # Copy all static files from afterpython/static/ to afterpython/_website/static/
    _move_files(ap.paths.static_path, website_static, is_copy=True)


@click.command(
    add_help_option=False,  # disable click's --help option so that ap build --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
@click.option(
    "--dev",
    is_flag=True,
    hidden=True,  # Internal flag used by `ap dev`, not exposed to users
    help="Development build - only build metadata for the landing page, skip content and production builds",
)
@click.option(
    "--execute", is_flag=True, help="Execute Jupyter notebooks for all content types"
)
def build(ctx, dev: bool, execute: bool):
    """Build the project website and all contents for production.

    This command builds MyST content (doc/blog/tutorial/example/guide) and the SvelteKit website.

    Any extra arguments are passed to the 'myst build --html' command for each content type.
    See "myst build --help" for more details.

    Use --execute to execute Jupyter notebooks for all content types.
    """
    from afterpython.utils import has_content_for_myst
    from afterpython.utils import handle_passthrough_help

    # Show both our options and myst's help and exit
    handle_passthrough_help(
        ctx,
        ["myst", "build"],
        show_underlying=True,
    )

    paths = ctx.obj["paths"]
    prebuild()

    # Determine BASE_PATH based on website URL configuration
    base_path = determine_base_path()
    if base_path:
        click.echo(f"Using BASE_PATH: {base_path}")
    else:
        click.echo("Using BASE_PATH: (empty - custom domain)")

    click.echo("Building metadata.json...")
    build_metadata()

    # myst's production build
    if not dev:
        node_env: NodeEnv = find_node_env()
        for content_type in CONTENT_TYPES:
            content_path = paths.afterpython_path / content_type
            if not has_content_for_myst(content_path):
                click.echo(f"Skipping {content_type}/ (no content files found)")
                continue

            click.echo(f"Building {content_type}/...")
            # NOTE: needs to set BASE_URL so that the project website can link to the content pages correctly at e.g. localhost:5173/doc
            base_url = f"{base_path}/{content_type}"
            build_env = {**node_env, "BASE_URL": base_url, "BASE_PATH": base_path}
            result = subprocess.run(
                [
                    "myst",
                    "build",
                    "--html",
                    *(["--execute"] if execute else []),
                    *ctx.args,
                ],
                cwd=content_path,
                env=build_env,
                check=False,
            )
            if result.returncode != 0:
                raise Exit(result.returncode)

    postbuild()

    # website's production build
    if not dev:
        click.echo("Building project website...")
        website_env = {**node_env, "BASE_PATH": base_path}
        result = subprocess.run(
            ["pnpm", "build"], cwd=paths.website_path, env=website_env, check=False
        )
        if result.returncode != 0:
            raise Exit(result.returncode)
