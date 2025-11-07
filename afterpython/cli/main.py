import click
from trogon import tui

from afterpython.cli.commands.init import init
from afterpython.cli.commands.build import build
from afterpython.cli.commands.dev import dev


@tui(command='tui', help="Open terminal UI")
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.version_option()
def afterpython_group(ctx):
    """afterpython's CLI"""
    ctx.ensure_object(dict)


afterpython_group.add_command(init)
afterpython_group.add_command(build)
afterpython_group.add_command(dev)