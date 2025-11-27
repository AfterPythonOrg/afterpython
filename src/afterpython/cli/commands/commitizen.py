import subprocess

import click
from click.exceptions import Exit


@click.command(
    add_help_option=False,  # disable click's --help option so that cz --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def commitizen(ctx):
    """Run commitizen CLI (uses afterpython/cz.toml)"""
    from afterpython.utils import handle_passthrough_help

    # Show both our options and commitizen's help and exit
    handle_passthrough_help(
        ctx,
        ["cz"],
        show_underlying=True,
    )

    paths = ctx.obj["paths"]
    cz_toml_path = paths.afterpython_path / "cz.toml"
    result = subprocess.run(
        ["cz", "--config", str(cz_toml_path), *ctx.args], check=False
    )
    if result.returncode != 0:
        raise Exit(result.returncode)
