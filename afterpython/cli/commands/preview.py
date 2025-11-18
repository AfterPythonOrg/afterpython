import subprocess

import click


@click.command()
@click.pass_context
def preview(ctx):
    """Preview the production build of the project website (including myst's builds)"""
    from afterpython.utils import find_node_env

    paths = ctx.obj["paths"]
    node_env = find_node_env()
    click.echo(
        "Previewing the production build of the project website (including myst's builds)..."
    )
    subprocess.run(
        ["pnpm", "preview"], cwd=paths.website_path, env=node_env, check=True
    )
