import subprocess

import click
from click.exceptions import Exit

from afterpython.utils import has_pixi, has_uv


@click.command()
@click.option(
    "--optional",
    type=str,
    default=None,
    required=False,
    help="Remove from an optional dependency group (pixi: mapped to 'optional' feature)",
)
@click.option(
    "--group",
    type=str,
    default=None,
    required=False,
    help="Remove from a dependency group (pixi: mapped to same-named feature)",
)
@click.argument("lib", type=str, required=True)
def remove(optional: str | None, group: str | None, lib: str):
    """Remove a dependency from the project (manages both uv and pixi if present)"""
    if not has_uv():
        click.echo("uv not found. Please install uv first.")
        return

    if optional and group:
        click.echo("Error: Cannot specify both --optional and --group")
        raise Exit(1)

    result = subprocess.run(
        [
            "uv",
            "remove",
            *(["--optional", optional] if optional else []),
            *(["--group", group] if group else []),
            lib,
        ],
        check=False,
    )
    if result.returncode != 0:
        raise Exit(result.returncode)

    if has_pixi():
        # NOTE: pixi doesn't support --optional, so we need to use --feature instead
        if optional:
            feature_name = "optional"
        elif group:
            feature_name = group
        else:
            feature_name = None
        result = subprocess.run(
            [
                "pixi",
                "remove",
                "--pypi",
                *(["--feature", feature_name] if feature_name else []),
                lib,
            ],
            check=False,
        )
        if result.returncode != 0:
            raise Exit(result.returncode)
