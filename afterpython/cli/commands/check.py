import subprocess

import click
from click.exceptions import Exit


@click.command(
    add_help_option=False,  # disable click's --help option so that ruff check --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def check(ctx):
    """Simple wrapper for ruff check for convenience, always use the afterpython/ruff.toml if it exists"""
    paths = ctx.obj["paths"]
    ruff_toml = paths.afterpython_path / "ruff.toml"
    if ruff_toml.exists():
        click.echo(f"Using ruff configuration from {ruff_toml}")
        result = subprocess.run(
            ["ruff", "check", "--config", str(ruff_toml), *ctx.args], check=False
        )
    else:
        result = subprocess.run(["ruff", "check", *ctx.args], check=False)
    if result.returncode != 0:
        raise Exit(result.returncode)
