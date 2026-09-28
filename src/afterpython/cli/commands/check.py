import subprocess

import click
from click.exceptions import Exit


@click.command(
    add_help_option=False,  # disable click's --help option so that ruff check --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def check(ctx):
    """Run ruff linter"""
    from afterpython.utils import handle_passthrough_help

    # Show both our options and ruff's help and exit
    handle_passthrough_help(
        ctx,
        ["ruff", "check"],
        show_underlying=True,
    )

    # no --config: ruff finds afterpython/ruff.toml via pyproject.toml's [tool.ruff] extend
    result = subprocess.run(["ruff", "check", *ctx.args], check=False)
    if result.returncode != 0:
        raise Exit(result.returncode)
