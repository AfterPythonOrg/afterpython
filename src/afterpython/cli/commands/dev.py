from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import contextlib
import os
import queue
import signal
import subprocess
import threading
import time

import click
from click.exceptions import Exit

from afterpython.cli.commands.build import postbuild, prebuild
from afterpython.const import CONTENT_TYPES
from afterpython.utils import find_available_port, find_node_env


def _stream_process_output(
    proc: subprocess.Popen,
    output_queue: queue.Queue[str | None],
    ready_event: threading.Event,
):
    """Forward process output to the terminal and queue startup lines."""
    if proc.stdout is None:
        if not ready_event.is_set():
            output_queue.put(None)
        return

    for line in proc.stdout:
        click.echo(line, nl=False)
        if not ready_event.is_set():
            output_queue.put(line)

    if not ready_event.is_set():
        output_queue.put(None)


def _wait_for_myst_server(
    proc: subprocess.Popen,
    content_type: str,
    port: int,
    output_queue: queue.Queue[str | None],
    ready_event: threading.Event,
    timeout: int = 300,
):
    """Wait until MyST reports that its dev server has started."""
    deadline = time.monotonic() + timeout
    ready_markers = (
        f"Server started on port {port}",
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
    )

    try:
        while time.monotonic() < deadline:
            returncode = proc.poll()
            if returncode is not None and output_queue.empty():
                if returncode == 0:
                    click.echo(
                        f"MyST {content_type} server exited before becoming ready"
                    )
                    return
                raise Exit(returncode)

            try:
                line = output_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if line is None:
                returncode = proc.poll()
                if returncode not in (None, 0):
                    raise Exit(returncode)
                click.echo(f"MyST {content_type} server exited before becoming ready")
                return

            if any(marker in line for marker in ready_markers):
                click.echo(f"MyST {content_type} server is ready")
                return

        raise click.ClickException(
            f"Timed out waiting for MyST {content_type} server on port {port}"
        )
    finally:
        ready_event.set()


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

    from afterpython.utils import handle_passthrough_help, is_website_initialized

    # Show both our options and myst's help and exit
    handle_passthrough_help(
        ctx,
        ["myst", "start"],
        show_underlying=True,
    )

    if not is_website_initialized():
        click.echo(
            "Website has not been initialized. Skipping dev server.\n"
            "Run 'ap update website' to initialize the website."
        )
        return

    # Track all MyST processes for cleanup
    myst_processes = []

    paths = ctx.obj["paths"]

    def cleanup_processes():
        """Clean up all MyST server processes.

        Each spawned 'ap {content_type}' is its own session leader (start_new_session=True
        below), so its grandchild `myst start` shares the same process group. proc.terminate()
        would only SIGTERM the outer Python wrapper — which is blocked in subprocess.run and
        doesn't forward the signal — leaving myst orphaned. Signal the whole group instead.
        """
        click.echo("\nShutting down MyST servers...")
        for proc in myst_processes:
            try:
                pgid = os.getpgid(proc.pid)
            except ProcessLookupError:
                continue
            try:
                os.killpg(pgid, signal.SIGTERM)
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
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
        prebuild()

        # Clear .env.development before writing new ports
        env_file = paths.website_path / ".env.development"
        env_file.write_text("")  # Clear existing content

        # myst development servers
        if enabled_content_types:
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

                output_queue: queue.Queue[str | None] = queue.Queue()
                ready_event = threading.Event()
                myst_process = subprocess.Popen(
                    [
                        "ap",
                        f"{content_type}",
                        "--port",
                        str(myst_port),
                        *(["--execute"] if execute else []),
                        *ctx.args,
                    ],
                    # New session so cleanup_processes can SIGTERM the whole group and
                    # take the grandchild `myst start` down with the wrapper.
                    start_new_session=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                myst_processes.append(myst_process)
                threading.Thread(
                    target=_stream_process_output,
                    args=(myst_process, output_queue, ready_event),
                    daemon=True,
                ).start()
                _wait_for_myst_server(
                    myst_process, content_type, myst_port, output_queue, ready_event
                )

        postbuild(dev_build=True)

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
            if myst_processes:
                # Keep the process running to maintain MyST servers
                click.echo("Press Ctrl+C to stop MyST servers...")
                while True:
                    time.sleep(1)
    except KeyboardInterrupt:
        # Handle Ctrl+C during subprocess.run
        pass
    finally:
        cleanup_processes()
