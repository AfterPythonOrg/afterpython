import os
import subprocess

import click
from trogon import tui
from dotenv import load_dotenv, find_dotenv

import afterpython as ap
from afterpython import __version__
from afterpython.cli.commands.init import init
from afterpython.cli.commands.build import build
from afterpython.cli.commands.dev import dev
from afterpython.cli.commands.update import update
from afterpython.cli.commands.check import check
from afterpython.cli.commands.format import format
from afterpython.cli.commands.sync import sync
from afterpython.cli.commands.start import start, doc, blog, tutorial, example, guide


@tui(command="tui", help="Open terminal UI")
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.version_option(version=__version__)
def afterpython_group(ctx):
    """afterpython's CLI"""
    load_dotenv(find_dotenv())  # Load environment variables from .env file
    ctx.ensure_object(dict)
    ctx.obj["paths"] = ap.paths

    # Auto-sync before commands (except sync itself to avoid recursion)
    if ctx.invoked_subcommand and ctx.invoked_subcommand not in ['sync', 'init'] and os.getenv("AP_AUTO_SYNC", "0") == "1":
        click.echo("Auto-syncing...")
        subprocess.run(["ap", "sync"])


afterpython_group.add_command(init)
afterpython_group.add_command(build)
afterpython_group.add_command(dev)
afterpython_group.add_command(update)
afterpython_group.add_command(check)
afterpython_group.add_command(format)
afterpython_group.add_command(sync)
afterpython_group.add_command(start)
afterpython_group.add_command(doc)
afterpython_group.add_command(doc, name="docs")
afterpython_group.add_command(blog)
afterpython_group.add_command(blog, name="blogs")
afterpython_group.add_command(tutorial)
afterpython_group.add_command(tutorial, name="tutorials")
afterpython_group.add_command(example)
afterpython_group.add_command(example, name="examples")
afterpython_group.add_command(guide)
afterpython_group.add_command(guide, name="guides")