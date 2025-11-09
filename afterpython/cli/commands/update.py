from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv
    from afterpython.pcu import NormalizedDependencies
    
import subprocess
import shutil

import click


@click.group()
def update():
    """Update pyproject.toml dependencies, website template etc."""
    pass


@update.command()
@click.pass_context
@click.option(
    "-u", "--upgrade",
    is_flag=True,
    help="if enabled, the dependencies will be upgraded to the latest version",
)
def dependencies(ctx, upgrade: bool):
    """Update pyproject.toml dependencies to the latest version"""
    from afterpython.pcu import get_dependencies, update_dependencies
    from afterpython.utils.utils import has_uv

    dependencies: NormalizedDependencies = get_dependencies(is_normalized=True)
    for dep_type in dependencies:
        # category = extras or group name
        click.echo(f"- {dep_type} package(s):")
        for category, deps in dependencies[dep_type].items():
            if dep_type == 'dependencies':
                category_name = ''
            elif dep_type == 'optional-dependencies':
                category_name = f"extras: {category}"
            elif dep_type == 'dependency-groups':
                category_name = f"group: {category}"
            else:
                raise ValueError(f"Invalid dependency type: {dep_type}")
            for dep in deps:
                msg = f"  {dep.requirement.name}: {dep.min_version}"
                has_update = dep.min_version != dep.latest_version
                if has_update:
                    msg += f" → {click.style(dep.latest_version, fg='green', bold=True)}"
                if category_name:
                    msg += f" ({category_name})"
                click.echo(msg)
    if upgrade:
        update_dependencies(dependencies)  # write the latest versions to pyproject.toml
        if has_uv():
            click.echo("Upgrading dependencies with uv...")
            subprocess.run(["uv", "lock"], check=True)
            subprocess.run(["uv", "sync", "--all-extras", "--all-groups"], check=True)
            click.echo(click.style("✓ All dependencies upgraded successfully 🎉", fg="green", bold=True))
        else:
            click.echo("uv not found. Updated pyproject.toml only (packages not installed).")
update.add_command(dependencies, name="deps")  # alias for "dependencies"


@update.command()
@click.pass_context
@click.option(
    "--no-backup",
    is_flag=True,
    help="if enabled, the existing project website template will not be backed up",
)
def website(ctx, no_backup: bool):
    """Update the project website template to the latest version"""
    from afterpython.utils.utils import find_node_env

    website_template_repo = "AfterPythonOrg/project-website-template"

    paths = ctx.obj["paths"]
    website_path = paths.website_path
    if not no_backup:
        backup_path = website_path.parent / "_website.backup"
        if backup_path.exists():
            click.echo(f"Removing old backup at {backup_path}...")
            shutil.rmtree(backup_path)
        if website_path.exists():
            click.echo(f"Creating backup at {backup_path}...")
            shutil.copytree(
                website_path,
                backup_path,
                ignore=shutil.ignore_patterns("node_modules", ".svelte-kit"),
            )

    # Remove old template (but keep node_modules for faster reinstall)
    if website_path.exists():
        click.echo("Removing old project website template...")
        shutil.rmtree(website_path)
    website_path.mkdir(parents=True, exist_ok=True)

    try:
        click.echo("Updating the project website template...")
        node_env: NodeEnv = find_node_env()
        subprocess.run(
            ["pnpx", "degit", website_template_repo, str(website_path)], env=node_env
        )
        subprocess.run(["pnpm", "install"], cwd=website_path, env=node_env, check=True)
    except Exception as e:
        click.echo(f"✗ Error updating project website template: {e}", err=True)
        if not no_backup:
            click.echo("Restoring from backup...")
            if website_path.exists():
                shutil.rmtree(website_path)
            shutil.copytree(backup_path, website_path)
        raise
