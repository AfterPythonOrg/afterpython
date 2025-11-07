from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import shutil
import subprocess

import click

from afterpython.const.paths import WEBSITE_PATH
from afterpython.utils.utils import find_node_env


WEBSITE_TEMPLATE_REPO = "AfterPythonOrg/project-website-template"


@click.command()
@click.option('--no-backup', is_flag=True, help='if enabled, the existing project website template will not be backed up')
def update_template(no_backup: bool):
    """Update the project website template to the latest version"""
    if not no_backup:
        backup_path = WEBSITE_PATH.parent / "_website.backup"
        if backup_path.exists():
            click.echo("Removing old backup...")
            shutil.rmtree(backup_path)
        if WEBSITE_PATH.exists():
            click.echo(f"Creating backup at {backup_path}...")
            shutil.copytree(
                WEBSITE_PATH, 
                backup_path, 
                ignore=shutil.ignore_patterns('node_modules', '.svelte-kit')
            )
        
    # Remove old template (but keep node_modules for faster reinstall)
    if WEBSITE_PATH.exists():
        click.echo("Removing old project website template...")
        shutil.rmtree(WEBSITE_PATH)
    WEBSITE_PATH.mkdir(parents=True, exist_ok=True)

    try:
        click.echo("Updating the project website template...")
        node_env: NodeEnv = find_node_env()
        subprocess.run(["pnpx", "degit", WEBSITE_TEMPLATE_REPO, str(WEBSITE_PATH)], env=node_env)
        subprocess.run(["pnpm", "install"], cwd=WEBSITE_PATH, env=node_env, check=True)
    except Exception as e:
        click.echo(f"✗ Error updating project website template: {e}", err=True)
        if not no_backup:
            click.echo("Restoring from backup...")
            if WEBSITE_PATH.exists():
                shutil.rmtree(WEBSITE_PATH)
            shutil.copytree(backup_path, WEBSITE_PATH)
        raise