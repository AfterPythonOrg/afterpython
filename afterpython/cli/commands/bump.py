import subprocess

import click


@click.command(
    add_help_option=False,  # disable click's --help option so that cz --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def bump(ctx):
    """Run 'cz bump'"""
    subprocess.run(["ap", "cz", "bump", *ctx.args])
