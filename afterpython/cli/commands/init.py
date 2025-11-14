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
from afterpython.utils import find_node_env, get_github_url


def init_pyproject():
    """Initialize pyproject.toml with sensible defaults
    - add [build-system] section with uv build backend (same as `uv init --package`)
    - add [project.urls] section with homepage, repository, and documentation URLs
    """
    import httpx
    from afterpython.utils import fetch_pypi_json, get_git_user_config
    from afterpython._io.toml import read_pyproject, write_pyproject, _to_tomlkit

    build_backend = "uv_build"

    async def fetch_build_backend_version() -> str | None:
        """Fetch the latest version of build backend package from PyPI."""
        async with httpx.AsyncClient() as client:
            data = await fetch_pypi_json(client, build_backend)
            return data["info"]["version"] if data else None

    data: TOMLDocument = read_pyproject()
    is_updated = False

    if "build-system" not in data:
        uv_build_version = asyncio.run(fetch_build_backend_version())
        if uv_build_version:
            data["build-system"] = {
                "requires": [f"{build_backend}>={uv_build_version}"],
                "build-backend": build_backend,
            }
            is_updated = True

    if "project" in data:
        if "urls" not in data["project"]:
            data["project"]["urls"] = {
                "homepage": "",
                "repository": get_github_url() or "",
                "documentation": "",
            }
            is_updated = True
        if "authors" not in data["project"]:
            # convert git user config to tomlkit object
            data["project"]["authors"] = _to_tomlkit([get_git_user_config()])
            is_updated = True

    if is_updated:
        write_pyproject(data)


def init_afterpython_toml():
    """Initialize afterpython.toml"""
    from afterpython._io.toml import update_afterpython

    afterpython_toml_path = ap.paths.afterpython_path / "afterpython.toml"
    if afterpython_toml_path.exists():
        click.echo(f"afterpython.toml already exists at {afterpython_toml_path}")
        return
    afterpython_toml_path.touch()
    update_afterpython(
        {
            "company": {
                "name": "",
                "url": "",
            }
        }
    )
    click.echo(f"Created {afterpython_toml_path}")


def init_mystmd():
    """
    Initialize MyST Markdown (mystmd) and myst.yml files in 
    docs, blogs, tutorials, examples, and guides directories with sensible defaults
    """
    from afterpython.const import CONTENT_TYPES
    from afterpython._io.yaml import update_myst_yml

    # find any existing node.js version and use it, if no, install the Node.js version specified in NODEENV_VERSION
    node_env: NodeEnv = find_node_env()
    subprocess.run(["npm", "install", "-g", "pnpm"], env=node_env, check=True)
    for content_type in CONTENT_TYPES:
        path = getattr(ap.paths, f"{content_type}_path")
        click.echo(f"Initializing MyST Markdown (mystmd) in {path.name} directory ...")
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["myst", "init"], cwd=path, input="n\n", text=True, env=node_env)
        myst_yml_defaults = {
            "extends": "../authors.yml",
            "project": {
                "license": "CC-BY-4.0",
                "subject": content_type.capitalize() if content_type != "doc" else "Documentation",
            },
            "site": {
                "options": {
                    "favicon": "../static/favicon.ico",
                    "logo": "../static/logo.svg",
                    "logo_dark": "../static/logo.svg",
                    "analytics_google": f"{{{'GOOGLE_ANALYTICS_ID'}}}",
                    # "twitter": "",
                },
            },
        }
        update_myst_yml(myst_yml_defaults, path)
        subprocess.run(["ap", "sync", "myst"])


def init_ruff_toml():
    afterpython_path = ap.paths.afterpython_path
    ruff_toml_path = afterpython_path / "ruff.toml"
    if ruff_toml_path.exists():
        click.echo(f"Ruff configuration file {ruff_toml_path} already exists")
        return
    ruff_template_path = ap.paths.package_path / "ruff-template.toml"
    shutil.copy(ruff_template_path, ruff_toml_path)
    click.echo(f"Created {ruff_toml_path}")


def init_authors_yml():
    """Initialize authors.yml by using authors in pyproject.toml"""
    from afterpython._io.toml import read_pyproject
    from afterpython._io.yaml import write_yaml, read_yaml

    data: TOMLDocument = read_pyproject()

    authors_yml_path = ap.paths.afterpython_path / "authors.yml"
    if authors_yml_path.exists():
        click.echo(f"Authors configuration file {authors_yml_path} already exists")
        return

    # read myst.yml from docs path to get "version"
    docs_myst_yml = read_yaml(ap.paths.docs_path / "myst.yml")
    yml_data = {
        "version": docs_myst_yml["version"],
        "project": {
            "contributors": [
                {
                    "id": str(author.get("name", "")).replace(" ", "_").lower(),
                    "name": str(author.get("name", "")),
                    "email": str(author.get("email", "")),
                }
                for author in data["project"]["authors"]
            ]
        },
    }
    write_yaml(authors_yml_path, yml_data)
    yml_data = read_yaml(authors_yml_path)
    yml_data["project"].yaml_set_comment_before_after_key(
        "contributors",
        after="See more at: https://mystmd.org/guide/frontmatter#frontmatter-authors",
    )
    write_yaml(authors_yml_path, yml_data)
    click.echo(f"Created {authors_yml_path}")


def init_website():
    click.echo(f"Initializing project website template in {ap.paths.website_path}...")
    subprocess.run(["ap", "update", "website"])


@click.command()
@click.pass_context
def init(ctx):
    """Initialize afterpython with MyST Markdown (by default) and project website template"""
    paths = ctx.obj["paths"]
    click.echo("Initializing afterpython...")
    afterpython_path = paths.afterpython_path
    static_path = paths.static_path

    afterpython_path.mkdir(parents=True, exist_ok=True)
    static_path.mkdir(parents=True, exist_ok=True)
    afterpython_path.joinpath("afterpython.toml").touch()

    init_pyproject()

    init_afterpython_toml()

    init_mystmd()

    init_authors_yml()

    # TODO: init faq.yml

    init_website()

    if click.confirm(f"\nCreate ruff.toml in {afterpython_path}?", default=True):
        init_ruff_toml()

