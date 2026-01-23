import subprocess

import click
from click.exceptions import Exit


@click.command()
@click.pass_context
def preview(ctx):
    """Preview the production build of the project website"""
    from afterpython.utils import find_node_env, is_website_initialized

    if not is_website_initialized():
        click.echo(
            "Website has not been initialized. Skipping preview.\n"
            "Run 'ap update website' to initialize the website."
        )
        return

    paths = ctx.obj["paths"]
    node_env = find_node_env()
    click.echo(
        "Previewing the production build of the project website (including myst's builds)..."
    )
    result = subprocess.run(
        ["pnpm", "preview"], cwd=paths.website_path, env=node_env, check=False
    )
    if result.returncode != 0:
        raise Exit(result.returncode)
