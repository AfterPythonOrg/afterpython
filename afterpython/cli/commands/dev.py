from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import time
import subprocess

import click
from click.exceptions import Exit

from afterpython.utils import find_node_env, find_available_port
from afterpython.const import CONTENT_TYPES


@click.command(
    add_help_option=False,  # disable click's --help option so that ap dev --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
@click.option(
    "--all",
    is_flag=True,
    help="Start the development server for all content types and the project website",
)
@click.option(
    "--doc",
    is_flag=True,
    help="Start the development server for documentation content",
)
@click.option(
    "--blog",
    is_flag=True,
    help="Start the development server for blog content",
)
@click.option(
    "--tutorial",
    is_flag=True,
    help="Start the development server for tutorial content",
)
@click.option(
    "--example",
    is_flag=True,
    help="Start the development server for example content",
)
@click.option(
    "--guide",
    is_flag=True,
    help="Start the development server for guide content",
)
@click.option(
    "--execute", is_flag=True, help="Execute Jupyter notebooks for all content types"
)
@click.option(
    "--no-website",
    "-n",
    is_flag=True,
    help="Skip running the website dev server (pnpm dev). Useful when you want to run pnpm dev manually with custom options.",
)
def dev(
    ctx,
    all: bool,
    doc: bool,
    blog: bool,
    tutorial: bool,
    example: bool,
    guide: bool,
    execute: bool,
    no_website: bool,
):
    """Run the development server for the project website.

    By default, runs only the website without any content servers.
    Use --all to start all content types, or specify individual content types with --doc, --blog, etc.

    Examples:
      ap dev              # Website only
      ap dev --all        # Website + all content types
      ap dev --doc        # Website + doc content
      ap dev --doc --blog # Website + doc and blog content

    Any extra arguments are passed to the MyST servers (via 'ap doc/blog/tutorial/example/guide' commands).
    See "myst start --help" for more details.

    Use --execute to execute Jupyter notebooks for all content types.

    Use --no-website to skip the automatic 'pnpm dev' command, allowing you to run it manually
    with custom Vite options in the afterpython/_website directory.
    """

    from afterpython.utils import handle_passthrough_help

    # Show both our options and myst's help and exit
    handle_passthrough_help(
        ctx,
        ["myst", "start"],
        show_underlying=True,
    )

    # Track all MyST processes for cleanup
    myst_processes = []

    paths = ctx.obj["paths"]

    # OPTIMIZE: should implement incremental build?
    subprocess.run(["ap", "build", "--dev"])

    def cleanup_processes():
        """Clean up all MyST server processes"""
        click.echo("\nShutting down MyST servers...")
        for proc in myst_processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception:
                pass

    # Determine which content types to run
    if all:
        enabled_content_types = set(CONTENT_TYPES)
    else:
        # Check individual flags
        content_flags = {
            "doc": doc,
            "blog": blog,
            "tutorial": tutorial,
            "example": example,
            "guide": guide,
        }
        assert set(content_flags.keys()) == set(CONTENT_TYPES), (
            "Incomplete content flags"
        )
        enabled_content_types = {ct for ct, flag in content_flags.items() if flag}

    try:
        if enabled_content_types:
            # Clear .env.development before writing new ports
            env_file = paths.website_path / ".env.development"
            env_file.write_text("")  # Clear existing content

            next_port = 3000
            for content_type in CONTENT_TYPES:
                # Skip content types that are not enabled
                if content_type not in enabled_content_types:
                    continue

                # Find available port for MyST server
                myst_port = find_available_port(start_port=next_port)
                next_port = myst_port + 1
                click.echo(
                    click.style(
                        f"Starting MyST {content_type} server on port {myst_port}...",
                        fg="green",
                    )
                )

                # Append port to .env.development for SvelteKit
                with open(env_file, "a") as f:
                    f.write(
                        f"PUBLIC_{content_type.upper()}_URL=http://localhost:{myst_port}\n"
                    )

                myst_process = subprocess.Popen(
                    [
                        "ap",
                        f"{content_type}",
                        "--port",
                        str(myst_port),
                        *(["--execute"] if execute else []),
                        *ctx.args,
                    ],
                    # stdout=subprocess.DEVNULL,  # Suppress output (optional)
                    # stderr=subprocess.DEVNULL,  # Suppress errors (optional)
                )
                myst_processes.append(myst_process)

                # NOTE: MyST internally uses additional ports beyond the one specified by --port.
                # Without this delay, multiple MyST servers may attempt to bind to the same internal port,
                # causing "address already in use" errors.
                time.sleep(3)

        if not no_website:
            node_env: NodeEnv = find_node_env()
            click.echo("Running the web dev server...")
            result = subprocess.run(
                ["pnpm", "dev"], cwd=paths.website_path, env=node_env, check=False
            )
            if result.returncode != 0:
                raise Exit(result.returncode)
        else:
            click.echo(
                "Skipping website dev server (--no-website flag). Run 'pnpm dev' manually in afterpython/_website/ with your custom options."
            )
            if enabled_content_types:
                # Keep the process running to maintain MyST servers
                click.echo("Press Ctrl+C to stop MyST servers...")
                while True:
                    time.sleep(1)
    except KeyboardInterrupt:
        # Handle Ctrl+C during subprocess.run
        pass
    finally:
        cleanup_processes()
