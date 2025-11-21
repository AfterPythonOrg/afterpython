import subprocess

import click
from click.exceptions import Exit


def _command_supports_config(command: str) -> bool:
    """Check if a pre-commit command supports --config flag by checking its help text."""
    try:
        result = subprocess.run(
            ["pre-commit", command, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        return "--config" in result.stdout
    except Exception:
        return False


@click.command(
    add_help_option=False,  # disable click's --help option so that pre-commit --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def pre_commit(ctx):
    """Run pre-commit, always use the afterpython/.pre-commit-config.yaml if it exists"""
    from afterpython.utils import handle_passthrough_help

    # Show both our options and pre-commit's help and exit
    handle_passthrough_help(
        ctx,
        ["pre-commit"],
        show_underlying=True,
    )

    args = ctx.args[:]
    paths = ctx.obj["paths"]

    # Find the first command in args (skip any flags that might come before the command)
    command: str | None = None
    command_idx: int | None = None
    for i, arg in enumerate(args):
        if not arg.startswith("-"):
            command = arg
            command_idx = i
            break

    # If we found a command and --config is not already specified
    if (
        command
        and command_idx is not None
        and "--config" not in args
        and _command_supports_config(command)
    ):
        pre_commit_path = paths.afterpython_path / ".pre-commit-config.yaml"
        # Insert --config right after the command
        args.insert(command_idx + 1, "--config")
        args.insert(command_idx + 2, str(pre_commit_path))

    result = subprocess.run(["pre-commit", *args], check=False)
    if result.returncode != 0:
        raise Exit(result.returncode)
