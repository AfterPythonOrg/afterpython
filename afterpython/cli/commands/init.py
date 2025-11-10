from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv
    from tomlkit.toml_document import TOMLDocument

import shutil
import asyncio
import subprocess

import click

import afterpython as ap
from afterpython.utils.utils import find_node_env


def init_pyproject():
    """Initialize pyproject.toml with sensible defaults
    - add [build-system] section with uv build backend (same as `uv init --package`)
    - add [project.urls] section with homepage, repository, and documentation URLs
    """
    import httpx
    from afterpython.utils.utils import read_pyproject, write_pyproject, fetch_pypi_json, get_github_url

    build_backend = 'uv_build'

    async def fetch_build_backend_version() -> str | None:
        """Fetch the latest version of build backend package from PyPI."""
        async with httpx.AsyncClient() as client:
            data = await fetch_pypi_json(client, build_backend)
            return data["info"]["version"] if data else None
    
    data: TOMLDocument = read_pyproject()
    is_updated = False
    
    if 'build-system' not in data:
        uv_build_version = asyncio.run(fetch_build_backend_version())
        if uv_build_version:
            data['build-system'] = {
                'requires': [f'{build_backend}>={uv_build_version}'],
                'build-backend': build_backend,
            }
            is_updated = True
    
    if 'project' in data and 'urls' not in data['project']:
        data['project']['urls'] = {
            'homepage': '',
            'repository': get_github_url() or '',
            'documentation': '',
        }
        is_updated = True

    if is_updated:
        write_pyproject(data)


def init_mystmd():
    docs_path = ap.paths.docs_path
    # find any existing node.js version and use it, if no, install the Node.js version specified in NODEENV_VERSION
    node_env: NodeEnv = find_node_env()
    click.echo(
        f"Initializing MyST Markdown (mystmd) for documentation in {docs_path}..."
    )
    docs_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["myst", "init"], cwd=docs_path, input="n\n", text=True, env=node_env
    )


def init_website():
    click.echo(f"Initializing project website template in {ap.paths.website_path}...")
    subprocess.run(["ap", "update", "website"])


def init_ruff_toml():
    afterpython_path = ap.paths.afterpython_path
    ruff_toml_path = afterpython_path / "ruff.toml"
    if ruff_toml_path.exists():
        click.echo(f"Ruff configuration file {ruff_toml_path} already exists")
        return
    ruff_template_path = afterpython_path / "ruff-template.toml"
    shutil.copy(ruff_template_path, ruff_toml_path)
    click.echo(f"Created {ruff_toml_path}")


@click.command()
@click.pass_context
@click.option(
    "--no-mystmd",
    is_flag=True,
    help="if enabled, MyST Markdown will not be initialized",
)
def init(ctx, no_mystmd: bool):
    """Initialize afterpython with MyST Markdown (by default) and project website template"""
    paths = ctx.obj["paths"]
    click.echo("Initializing afterpython...")
    afterpython_path = paths.afterpython_path
    website_path = paths.website_path
    static_path = paths.static_path

    afterpython_path.mkdir(parents=True, exist_ok=True)
    static_path.mkdir(parents=True, exist_ok=True)
    afterpython_path.joinpath("afterpython.toml").touch()
    
    init_pyproject()
    
    if not no_mystmd:
        init_mystmd()

    if click.confirm(f"\nCreate project website in {website_path}?", default=True):
        init_website()

    if click.confirm(f"\nCreate ruff.toml in {afterpython_path}?", default=True):
        init_ruff_toml()