from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import subprocess

import click

from afterpython.utils import find_node_env, find_available_port
from afterpython.const import CONTENT_TYPES


@click.command()
@click.pass_context
def dev(ctx):
    """Run the development server for the project website"""
    paths = ctx.obj["paths"]
    # OPTIMIZE: should implement incremental build?
    subprocess.run(["ap", "build", "--only-contents"], check=True)

    # Clear .env.development before writing new ports
    env_file = paths.website_path / ".env.development"
    env_file.write_text("")  # Clear existing content

    # Track all MyST processes for cleanup
    myst_processes = []

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
        for content_type in CONTENT_TYPES:
            content_path = paths.afterpython_path / content_type

            # Check if directory has any content files
            has_content = any(
                content_path.glob('*.md') or
                content_path.glob('*.ipynb') or
                content_path.glob('*.tex')
            )

            if not has_content:
                click.echo(f"Skipping {content_type}/ (no content files found)")
                continue

            # Find available port for MyST server
            myst_port = find_available_port(start_port=3000)
            click.echo(f"Starting MyST {content_type} server on port {myst_port}...")

            # Append port to .env.development for SvelteKit
            with open(env_file, 'a') as f:
                f.write(f"PUBLIC_{content_type.upper()}_URL=http://localhost:{myst_port}\n")

            myst_process = subprocess.Popen(
                ["ap", f"{content_type}", "--port", str(myst_port)],
                # stdout=subprocess.DEVNULL,  # Suppress output (optional)
                # stderr=subprocess.DEVNULL,  # Suppress errors (optional)
            )
            myst_processes.append(myst_process)

        node_env: NodeEnv = find_node_env()
        click.echo("Running the web dev server...")
        subprocess.run(["pnpm", "dev"], cwd=paths.website_path, env=node_env, check=True)
    except KeyboardInterrupt:
        # Handle Ctrl+C during subprocess.run
        pass
    finally:
        cleanup_processes()
