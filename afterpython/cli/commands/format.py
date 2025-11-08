import subprocess

import click


@click.command(
    add_help_option=False,  # disable click's --help option so that ruff format --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.pass_context
def format(ctx):
    """Simple wrapper for ruff format for convenience"""
    subprocess.run(["ruff", "format", *ctx.args])
