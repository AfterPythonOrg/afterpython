from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import os
import subprocess


NODEENV_VERSION = "24.11.0"


def find_node_env() -> NodeEnv:
    '''
    Find if there is an installed Node.js version, if yes, use it
    If no, install the Node.js version specified in NODEENV_VERSION
    '''
    from mystmd_py.nodeenv import find_any_node
    # from mystmd_py.main import ensure_valid_version
    # Use mystmd's own node-finding logic
    binary_path = os.environ.get("PATH", os.defpath)
    node_path, os_path = find_any_node(binary_path, nodeenv_version=NODEENV_VERSION)
    node_env: NodeEnv = {**os.environ, "PATH": os_path}
    subprocess.run(["npm", "install", "-g", "pnpm"], env=node_env, check=True)
    return node_env