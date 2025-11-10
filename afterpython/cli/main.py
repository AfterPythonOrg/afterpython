import click
from dotenv import load_dotenv
from trogon import tui

import afterpython as ap
from afterpython import __version__
from afterpython.cli.commands.init import init
from afterpython.cli.commands.build import build
from afterpython.cli.commands.dev import dev
from afterpython.cli.commands.update import update
from afterpython.cli.commands.check import check
from afterpython.cli.commands.format import format


@tui(command="tui", help="Open terminal UI")
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.version_option(version=__version__)
def afterpython_group(ctx):
    """afterpython's CLI"""
    load_dotenv()  # Load environment variables from .env file
    ctx.ensure_object(dict)
    ctx.obj["paths"] = ap.paths


afterpython_group.add_command(init)
afterpython_group.add_command(build)
afterpython_group.add_command(dev)
afterpython_group.add_command(update)
afterpython_group.add_command(check)
afterpython_group.add_command(format)
