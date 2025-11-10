from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient
    from tomlkit.toml_document import TOMLDocument
    from afterpython._typing import NodeEnv

import os
import shutil
import subprocess

import tomlkit

import afterpython as ap


NODEENV_VERSION = "24.11.0"


def find_node_env() -> NodeEnv:
    """
    Find if there is an installed Node.js version, if yes, use it
    If no, install the Node.js version specified in NODEENV_VERSION
    """
    from mystmd_py.nodeenv import find_any_node

    # from mystmd_py.main import ensure_valid_version
    # Use mystmd's own node-finding logic
    binary_path = os.environ.get("PATH", os.defpath)
    node_path, os_path = find_any_node(binary_path, nodeenv_version=NODEENV_VERSION)
    node_env: NodeEnv = {**os.environ, "PATH": os_path}
    subprocess.run(["npm", "install", "-g", "pnpm"], env=node_env, check=True)
    return node_env


def has_uv() -> bool:
    """Check if uv is installed"""
    return shutil.which("uv") is not None


def read_pyproject() -> TOMLDocument:
    '''Read pyproject.toml'''
    with open(ap.paths.pyproject_path, "rb") as f:
        data: TOMLDocument = tomlkit.parse(f.read())
    return data


def write_pyproject(data: TOMLDocument):
    with open(ap.paths.pyproject_path, "w") as f:
        f.write(tomlkit.dumps(data))


async def fetch_pypi_json(client: AsyncClient, package_name: str) -> dict | None:
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        # Return None if package doesn't exist or network fails
        print(f"Warning: Could not fetch PyPI JSON for {package_name}: {e}")
        return None


def get_github_url() -> str | None:
    """Get GitHub repository URL from git remote origin."""
    import re
    
    try:
        from git import Repo
        
        # Get the repo
        repo = Repo(search_parent_directories=True)
        
        # Get origin remote URL
        if 'origin' not in repo.remotes:
            return None
            
        remote_url = repo.remotes.origin.url
        # Verify it's a GitHub URL
        if 'github.com' not in remote_url:
            return None
        
        # Convert SSH format to HTTPS format
        # git@github.com:user/repo.git -> https://github.com/user/repo
        if remote_url.startswith("git@github.com:"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")
        
        # Remove .git suffix if present
        remote_url = re.sub(r'\.git$', '', remote_url)
        
        return remote_url
        
    except (ImportError, Exception):
        # GitPython not installed or not in a git repo
        return None