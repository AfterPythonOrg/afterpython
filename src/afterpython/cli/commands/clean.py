from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import shutil
import subprocess

import click
from click.exceptions import Exit

from afterpython.const import CONTENT_TYPES
from afterpython.utils import find_node_env, has_content_for_myst


@click.command(
    add_help_option=False,  # disable click's --help option so that ap clean --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
@click.option(
    "--all",
    is_flag=True,
    help="Also clean AfterPython build directories (_build/ and _website/build/)",
)
def clean(ctx, all: bool):
    """Clean build artifacts from content types and website"""
    from afterpython.utils import handle_passthrough_help

    # Show both our options and myst's help and exit
    handle_passthrough_help(
        ctx,
        ["myst", "clean"],
        show_underlying=True,
    )

    paths = ctx.obj["paths"]
    node_env: NodeEnv = find_node_env()

    # Clean MyST builds for each content type
    for content_type in CONTENT_TYPES:
        content_path = paths.afterpython_path / content_type

        # Skip if no content exists
        if not has_content_for_myst(content_path):
            click.echo(f"Skipping {content_type}/ (no content found)")
            continue

        click.echo(f"Cleaning {content_type}/...")
        # Pass through any extra args to myst clean (e.g., --cache, --templates)
        result = subprocess.run(
            ["myst", "clean", *ctx.args, *(["--all"] if all else [])],
            cwd=content_path,
            env=node_env,
            check=False,
        )
        if result.returncode != 0:
            raise Exit(result.returncode)

    # Clean afterpython's build directories if --all flag is used
    if all:
        click.echo("Cleaning afterpython build directories...")

        # Clean _build/
        build_path = paths.build_path
        if build_path.exists():
            shutil.rmtree(build_path)
            click.echo(f"  Removed: {build_path}")

        # Clean _website/build/
        website_build = paths.website_path / "build"
        if website_build.exists():
            shutil.rmtree(website_build)
            click.echo(f"  Removed: {website_build}")

        click.echo("Done cleaning all build directories!")
    else:
        click.echo(
            "Done! Use 'ap clean --all' to also remove afterpython build directories."
        )
