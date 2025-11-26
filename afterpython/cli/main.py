import os
import subprocess
from collections import defaultdict

import click
from dotenv import find_dotenv, load_dotenv
from trogon import tui

import afterpython as ap
from afterpython import __version__
from afterpython.cli.commands.add import add
from afterpython.cli.commands.build import build
from afterpython.cli.commands.bump import bump
from afterpython.cli.commands.check import check
from afterpython.cli.commands.clean import clean
from afterpython.cli.commands.commit import commit
from afterpython.cli.commands.commitizen import commitizen
from afterpython.cli.commands.dev import dev
from afterpython.cli.commands.format import format
from afterpython.cli.commands.init import init
from afterpython.cli.commands.init_branch_rules import init_branch_rules
from afterpython.cli.commands.install import install
from afterpython.cli.commands.lock import lock
from afterpython.cli.commands.pre_commit import pre_commit
from afterpython.cli.commands.preview import preview
from afterpython.cli.commands.release import release
from afterpython.cli.commands.remove import remove
from afterpython.cli.commands.start import blog, doc, example, guide, start, tutorial
from afterpython.cli.commands.sync import sync
from afterpython.cli.commands.update import update


class AliasGroup(click.Group):
    """Custom group that displays command aliases together."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aliases = defaultdict(list)  # Maps primary command -> list of aliases
        self._alias_to_primary = {}  # Maps alias -> primary command name

    def add_command(self, cmd, name=None):
        """Track aliases when the same command is added with different names."""
        name = name or cmd.name

        # Check if this command object was already added under a different name
        for existing_name, existing_cmd in self.commands.items():
            if existing_cmd is cmd and existing_name != name:
                # This is an alias
                self._aliases[existing_name].append(name)
                self._alias_to_primary[name] = existing_name
                break

        super().add_command(cmd, name)

    def format_commands(self, ctx, formatter):
        """Format commands with aliases shown together."""
        commands = []
        for subcommand in self.list_commands(ctx):
            # Skip aliases - they'll be shown with their primary command
            if subcommand in self._alias_to_primary:
                continue

            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue

            # Skip hidden commands
            if cmd.hidden:
                continue

            help_text = cmd.get_short_help_str(limit=formatter.width)

            # Build command name with aliases
            aliases = self._aliases.get(subcommand, [])
            if aliases:
                subcommand = f"{subcommand}, {', '.join(aliases)}"

            commands.append((subcommand, help_text))

        if commands:
            with formatter.section("Commands"):
                formatter.write_dl(commands)


@tui(command="tui", help="Open terminal UI")
@click.group(cls=AliasGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.version_option(version=__version__)
def afterpython_group(ctx):
    """afterpython's CLI"""
    load_dotenv(find_dotenv())  # Load environment variables from .env file
    ctx.ensure_object(dict)
    ctx.obj["paths"] = ap.paths

    # Auto-sync before commands (except sync itself to avoid recursion)
    if (
        ctx.invoked_subcommand
        and ctx.invoked_subcommand not in ["sync", "init"]
        and os.getenv("AP_AUTO_SYNC", "0") == "1"
    ):
        click.echo("Auto-syncing...")
        subprocess.run(["ap", "sync"])


afterpython_group.add_command(init)
afterpython_group.add_command(build)
afterpython_group.add_command(dev)
afterpython_group.add_command(update)
afterpython_group.add_command(check)
afterpython_group.add_command(check, name="lint")
afterpython_group.add_command(format)
afterpython_group.add_command(sync)
afterpython_group.add_command(start)
afterpython_group.add_command(install)
afterpython_group.add_command(doc)
afterpython_group.add_command(blog)
afterpython_group.add_command(tutorial)
afterpython_group.add_command(example)
afterpython_group.add_command(guide)
afterpython_group.add_command(preview)
afterpython_group.add_command(clean)
afterpython_group.add_command(pre_commit)
afterpython_group.add_command(pre_commit, name="pc")
afterpython_group.add_command(commitizen)
afterpython_group.add_command(commitizen, name="cz")
afterpython_group.add_command(commit)
afterpython_group.add_command(bump)
afterpython_group.add_command(release)
afterpython_group.add_command(init_branch_rules)
afterpython_group.add_command(add)
afterpython_group.add_command(remove)
afterpython_group.add_command(lock)
