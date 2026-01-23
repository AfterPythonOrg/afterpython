from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from httpx import AsyncClient

    from afterpython._typing import NodeEnv

import os
import re
import shutil
import subprocess

import click


def find_node_env() -> NodeEnv:
    """
    Find if there is an installed Node.js version, if yes, use it
    If no, install the Node.js version specified in NODEENV_VERSION
    """
    from mystmd_py.nodeenv import find_any_node

    from afterpython.const import NODEENV_VERSION

    # from mystmd_py.main import ensure_valid_version
    # Use mystmd's own node-finding logic
    binary_path = os.environ.get("PATH", os.defpath)
    _node_path, os_path = find_any_node(binary_path, nodeenv_version=NODEENV_VERSION)
    node_env: NodeEnv = {**os.environ, "PATH": os_path}
    return node_env


def has_uv() -> bool:
    """Check if uv is installed"""
    return shutil.which("uv") is not None


def has_pixi() -> bool:
    """Check if pixi is installed"""
    return shutil.which("pixi") is not None


def has_gh() -> bool:
    """Check if gh is installed"""
    return shutil.which("gh") is not None


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


# VIBE-CODED
def detect_license_from_file(file_path: str) -> str:
    """Extract license name from LICENSE file using regex."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Common license patterns
    patterns = {
        "Apache-2.0": r"Apache License\s+Version 2\.0",
        "MIT": r"MIT License|Permission is hereby granted, free of charge",
        "GPL-3.0": r"GNU GENERAL PUBLIC LICENSE\s+Version 3",
        "GPL-2.0": r"GNU GENERAL PUBLIC LICENSE\s+Version 2",
        "BSD-3-Clause": r"BSD 3-Clause License|Redistribution and use in source and binary forms",
        "BSD-2-Clause": r"BSD 2-Clause License",
        "ISC": r"ISC License",
        "LGPL-3.0": r"GNU LESSER GENERAL PUBLIC LICENSE\s+Version 3",
        "MPL-2.0": r"Mozilla Public License Version 2\.0",
    }

    # Check first 500 chars for license header
    header = content[:500]

    for license_id, pattern in patterns.items():
        if re.search(pattern, header, re.IGNORECASE):
            return license_id

    return ""


def deep_merge(base: dict, updates: dict, extend_lists: bool = True) -> dict:
    """Deep merge updates into base, preserving structure and metadata.

    Works with:
    - Regular Python dicts
    - tomlkit TOMLDocument/Table objects
    - ruamel.yaml CommentedMap objects

    Behavior:
    - Dicts are merged recursively
    - Lists are extended (concatenated)
    - Other types are overwritten

    Args:
        base: The base dictionary to merge into (modified in-place)
        updates: The updates to apply

    Returns:
        The merged base dictionary (same object, modified in-place)
    """
    for key, value in updates.items():
        if key in base:
            if isinstance(base[key], dict) and isinstance(value, dict):
                # Recursively merge dicts
                deep_merge(base[key], value, extend_lists=extend_lists)
            elif (
                isinstance(base[key], list) and isinstance(value, list) and extend_lists
            ):
                # Extend lists, but only add items that don't already exist
                for item in value:
                    if item not in base[key]:
                        base[key].append(item)
            else:
                # Overwrite for other types
                base[key] = value
        else:
            base[key] = value

    return base


def convert_author_name_to_id(name: str) -> str:
    """Convert author name to ID

    Args:
        name: The author name

    Returns:
        The author ID

    Examples:
        - "Stephen Yau" -> "stephen_yau"
        - "John Doe" -> "john_doe"
        - "Jane Smith" -> "jane_smith"
    """
    return name.replace(" ", "_").lower()


def find_available_port(
    start_port: int = 3000, max_port: int = 3100, host: str = "localhost"
) -> int:
    """
    Find a TCP port with no listener on `host`, starting from start_port.
    """
    import socket

    def is_port_in_use(
        port: int, host: str = "localhost", timeout: float = 0.2
    ) -> bool:
        """
        Return True if *any* TCP listener is active on the given host:port.
        This works across IPv4/IPv6 by using getaddrinfo().
        """
        try:
            for family, socktype, proto, _canonname, sockaddr in socket.getaddrinfo(
                host, port, type=socket.SOCK_STREAM
            ):
                with socket.socket(family, socktype, proto) as s:
                    s.settimeout(timeout)
                    if s.connect_ex(sockaddr) == 0:
                        return True
        except socket.gaierror:
            # host couldn't be resolved; treat as no listener
            return False
        return False

    for port in range(start_port, max_port + 1):
        if not is_port_in_use(port, host=host):
            return port
    raise RuntimeError(
        f"No free ports available in range {start_port}-{max_port} for host={host!r}"
    )


def has_content_for_myst(content_path: Path) -> bool:
    """Check if a content directory has any content files"""
    return any(
        content_path.glob("*.md")
        or content_path.glob("*.ipynb")
        or content_path.glob("*.tex")
    )


def handle_passthrough_help(
    ctx: click.Context,
    underlying_command: list[str],
    show_underlying: bool = True,
    help_flags: tuple[str, ...] = ("--help", "-h"),
) -> None:
    """Handle --help for commands that pass through to underlying tools.

    Shows both Click's help (custom options) and the underlying tool's help.

    Args:
        ctx: Click context
        underlying_command: Command to show help for (e.g., ["cz", "bump"])
        show_underlying: Whether to show underlying tool's help (default: True)
        help_flags: Flags that trigger help display (default: ("--help", "-h"))
                   Use ("--help",) if -h is reserved by the underlying tool
    """
    # Check if any help flag is present
    if any(flag in ctx.args for flag in help_flags):
        # Show Click's help first (our custom options)
        click.echo(ctx.get_help())

        # Then show underlying tool's help if requested
        if show_underlying:
            click.echo("\n" + "=" * 60)
            click.echo(f"Additional options from '{' '.join(underlying_command)}':")
            click.echo("=" * 60 + "\n")
            subprocess.run([*underlying_command, "--help"])

        ctx.exit(0)


def normalize_static_path(path: str) -> str:
    """
    Normalize paths for static assets.

    Only allows two formats:
    1. Pure filename/path without ./ or ../ (e.g., "logo.svg", "somewhere/logo.svg")
    2. Absolute path starting with / (e.g., "/somewhere/logo.svg")

    Args:
        path: User-provided path from afterpython.toml

    Returns:
        Normalized path

    Raises:
        ValueError: If path contains ./ or ../ or other invalid patterns

    Examples:
        >>> normalize_static_path("logo.svg")
        'logo.svg'
        >>> normalize_static_path("somewhere/logo.svg")
        '/somewhere/logo.svg'
        >>> normalize_static_path("/somewhere/logo.svg")
        '/somewhere/logo.svg'
        >>> normalize_static_path("./logo.svg")  # Raises ValueError
        >>> normalize_static_path("../logo.svg")  # Raises ValueError
        >>> normalize_static_path("static/logo.svg")  # Raises ValueError
    """
    if not path:
        return ""

    # Reject paths with ./ or ../
    if "./" in path or "../" in path or path.startswith(".") or path.startswith(".."):
        raise ValueError(
            f"Invalid path '{path}': paths cannot contain './' or '../'. "
            f"Use either a pure filename (e.g., 'logo.svg') or absolute path (e.g., '/somewhere/logo.svg')"
        )

    # Reject paths with 'static' in them
    if "static" in path.lower():
        raise ValueError(
            f"Invalid path '{path}': do not include 'static' in the path. "
            f"Files are assumed to be in the static/ directory."
        )

    # If it starts with /, it's absolute - keep as is
    if not path.startswith("/"):
        return "/" + path
    else:
        return path


def get_relative_static_prefix(file_path: Path, content_type_path: Path) -> str:
    """Calculate the relative path prefix from a file to its content type's static/ folder.

    Args:
        file_path: Path to the content file (e.g., blog/layer/blog5.ipynb)
        content_type_path: Path to the content type folder (e.g., blog/)

    Returns:
        Relative prefix to reach static/ (e.g., "./" or "../" or "../../")
    """
    # Get the depth: how many directories deep the file is from content_type_path
    relative = file_path.parent.relative_to(content_type_path)
    depth = len(relative.parts)

    # Build the correct prefix
    if depth == 0:
        return "./"  # File is directly in content_type_path
    else:
        return "../" * depth


def is_website_initialized() -> bool:
    """Check if the website has been initialized.

    Returns:
        True if the website is initialized (afterpython/_website exists and has package.json)
        False otherwise
    """
    import afterpython as ap

    website_path = ap.paths.website_path
    package_json = website_path / "package.json"

    return website_path.exists() and package_json.exists()


def ensure_website_gitignore_rules() -> None:
    """Ensure website-related gitignore rules are present in the project's .gitignore.

    Adds the following rules if they don't exist:
    - **/_build/ (ignore all build directories)
    - !afterpython/_website/src/lib/ (un-ignore website source for customization)
    - afterpython/_website.backup/ (ignore backup created by ap update website)
    """
    import afterpython as ap

    gitignore_path = ap.paths.user_path / ".gitignore"

    # Rules that should be present
    required_rules = [
        "**/_build/",
        "!afterpython/_website/src/lib/",
        "afterpython/_website.backup/",
    ]

    # Read existing gitignore or create empty list
    if gitignore_path.exists():
        existing_lines = gitignore_path.read_text().splitlines()
    else:
        existing_lines = []

    # Find which rules are missing
    missing_rules = []
    for rule in required_rules:
        # Check if rule exists (exact match or as part of a line)
        if not any(rule in line for line in existing_lines):
            missing_rules.append(rule)

    # Add missing rules if any
    if missing_rules:
        # Ensure file ends with newline if it exists and has content
        content = gitignore_path.read_text() if gitignore_path.exists() else ""
        if content and not content.endswith("\n"):
            content += "\n"

        # Add a section header if we're adding rules
        if content:
            content += "\n"
        content += "# AfterPython website rules\n"
        content += "\n".join(missing_rules) + "\n"

        gitignore_path.write_text(content)
        click.echo(f"Added website-related rules to {gitignore_path}")
    else:
        click.echo("Website gitignore rules already present")
