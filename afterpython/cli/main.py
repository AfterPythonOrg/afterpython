import click
from trogon import tui

from afterpython.cli.commands.init import init
from afterpython.cli.commands.build import build
from afterpython.cli.commands.dev import dev
from afterpython.cli.commands.update_website import update_website
from afterpython.cli.commands.check import check
from afterpython.cli.commands.format import format


@tui(command="tui", help="Open terminal UI")
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.version_option()
def afterpython_group(ctx):
    """afterpython's CLI"""
    from afterpython._paths import Paths
    ctx.ensure_object(dict)
    ctx.obj["paths"] = Paths()


afterpython_group.add_command(init)
afterpython_group.add_command(build)
afterpython_group.add_command(dev)
afterpython_group.add_command(update_website)
afterpython_group.add_command(check)
afterpython_group.add_command(format)
