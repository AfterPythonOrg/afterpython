from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import time
import subprocess

import click

from afterpython.utils import find_node_env, find_available_port
from afterpython.const import CONTENT_TYPES


@click.command()
@click.pass_context
@click.option('--all', is_flag=True, help='Start the development server for all content types and the project website')
def dev(ctx, all: bool):
    """Run the development server for the project website
    if --all is enabled, start the development server for all content types and the project website
    """
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

    try:
        paths = ctx.obj["paths"]

        # OPTIMIZE: should implement incremental build?
        subprocess.run(["ap", "build", "--dev"], check=True)
        
        if all:
            # Clear .env.development before writing new ports
            env_file = paths.website_path / ".env.development"
            env_file.write_text("")  # Clear existing content

            # Track all MyST processes for cleanup
            myst_processes = []

            next_port = 3000
            for content_type in CONTENT_TYPES:
                # Find available port for MyST server
                myst_port = find_available_port(start_port=next_port)
                next_port = myst_port + 1
                click.echo(click.style(f"Starting MyST {content_type} server on port {myst_port}...", fg="green"))

                # Append port to .env.development for SvelteKit
                with open(env_file, 'a') as f:
                    f.write(f"PUBLIC_{content_type.upper()}_URL=http://localhost:{myst_port}\n")

                myst_process = subprocess.Popen(
                    ["ap", f"{content_type}", "--port", str(myst_port)],
                    # stdout=subprocess.DEVNULL,  # Suppress output (optional)
                    # stderr=subprocess.DEVNULL,  # Suppress errors (optional)
                )
                myst_processes.append(myst_process)

                # NOTE: MyST internally uses additional ports beyond the one specified by --port.
                # Without this delay, multiple MyST servers may attempt to bind to the same internal port,
                # causing "address already in use" errors.
                time.sleep(3)
        
        node_env: NodeEnv = find_node_env()
        click.echo("Running the web dev server...")
        subprocess.run(["pnpm", "dev"], cwd=paths.website_path, env=node_env, check=True)
    except KeyboardInterrupt:
        # Handle Ctrl+C during subprocess.run
        pass
    finally:
        cleanup_processes()
