import os
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
@click.option(
    "--no-cz", "--no-commitizen", is_flag=True, help="Skip running 'cz commit'"
)
def commit(ctx, no_cz: bool):
    """Run 'cz commit'"""
    from afterpython.utils import handle_passthrough_help

    # Show both our options and commitizen's help and exit
    handle_passthrough_help(
        ctx,
        ["cz", "commit"],
        show_underlying=True,
    )

    if not no_cz:
        subprocess.run(["ap", "cz", "commit", *ctx.args])
    else:
        env = os.environ.copy()
        env["SKIP"] = "commitizen,commitizen-branch"
        subprocess.run(["git", "commit", *ctx.args], env=env)
