from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tomlkit.toml_document import TOMLDocument

import asyncio

from pyproject_metadata import StandardMetadata

import afterpython as ap
from afterpython._io.toml import read_toml, write_toml, _to_tomlkit


def read_pyproject() -> TOMLDocument:
    '''Read pyproject.toml'''
    return read_toml(ap.paths.pyproject_path)


def write_pyproject(data: TOMLDocument):
    write_toml(ap.paths.pyproject_path, data)


def read_metadata() -> StandardMetadata:
    '''Read metadata from pyproject.toml'''
    return StandardMetadata.from_pyproject(read_pyproject())


def init_pyproject():
    """Initialize pyproject.toml with sensible defaults
    - add [build-system] section with uv build backend (same as `uv init --package`)
    - add [project.urls] section with homepage, repository, and documentation URLs
    """
    import httpx
    from afterpython.utils import fetch_pypi_json
    from afterpython.tools._git import get_git_user_config, get_github_url

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