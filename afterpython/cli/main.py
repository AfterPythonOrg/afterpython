import click
from trogon import tui

from afterpython.cli.commands.test import test


@tui(command='tui', help="Open terminal UI")
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.version_option()
def afterpython_group(ctx):
    """afterpython's CLI"""
    ctx.ensure_object(dict)


afterpython_group.add_command(test)
