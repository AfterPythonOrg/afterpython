from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient
    from afterpython._typing import NodeEnv

import os
import re
import shutil


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
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    
    # Common license patterns
    patterns = {
        'Apache-2.0': r'Apache License\s+Version 2\.0',
        'MIT': r'MIT License|Permission is hereby granted, free of charge',
        'GPL-3.0': r'GNU GENERAL PUBLIC LICENSE\s+Version 3',
        'GPL-2.0': r'GNU GENERAL PUBLIC LICENSE\s+Version 2',
        'BSD-3-Clause': r'BSD 3-Clause License|Redistribution and use in source and binary forms',
        'BSD-2-Clause': r'BSD 2-Clause License',
        'ISC': r'ISC License',
        'LGPL-3.0': r'GNU LESSER GENERAL PUBLIC LICENSE\s+Version 3',
        'MPL-2.0': r'Mozilla Public License Version 2\.0',
    }
    
    # Check first 500 chars for license header
    header = content[:500]
    
    for license_id, pattern in patterns.items():
        if re.search(pattern, header, re.IGNORECASE):
            return license_id
    
    return ''


def deep_merge(base: dict, updates: dict) -> dict:
    """Deep merge updates into base, preserving structure and metadata.
    
    Works with:
    - Regular Python dicts
    - tomlkit TOMLDocument/Table objects  
    - ruamel.yaml CommentedMap objects
    
    Args:
        base: The base dictionary to merge into (modified in-place)
        updates: The updates to apply
        
    Returns:
        The merged base dictionary (same object, modified in-place)
    """
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
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


def find_available_port(start_port: int = 3000, max_port: int = 3100, host: str = "localhost") -> int:
    """
    Find a TCP port with no listener on `host`, starting from start_port.
    """
    import socket
    def is_port_in_use(port: int, host: str = "localhost", timeout: float = 0.2) -> bool:
        """
        Return True if *any* TCP listener is active on the given host:port.
        This works across IPv4/IPv6 by using getaddrinfo().
        """
        try:
            for family, socktype, proto, canonname, sockaddr in socket.getaddrinfo(
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
    raise RuntimeError(f"No free ports available in range {start_port}-{max_port} for host={host!r}")
