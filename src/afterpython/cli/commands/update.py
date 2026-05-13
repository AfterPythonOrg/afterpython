from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv
    from afterpython.pcu import Dependencies

import shutil
import subprocess

import click
from click.exceptions import Exit


@click.group()
def update():
    """Update website template, pyproject.toml dependencies, etc."""
    pass


@update.command()
@click.option(
    "-u",
    "--upgrade",
    is_flag=True,
    help="Upgrade dependencies to their latest versions",
)
@click.option(
    "--all",
    "all_",
    is_flag=True,
    help="Also update pre-commit hooks and pixi dependencies",
)
@click.option(
    "--exclude",
    "exclude",
    multiple=True,
    metavar="PACKAGE",
    help="Package to exclude from upgrade (can be passed multiple times)",
)
def dependencies(upgrade: bool, all_: bool, exclude: tuple[str, ...]):
    """Check and update project dependencies to latest versions"""
    from afterpython.pcu import get_dependencies, update_dependencies
    from afterpython.utils import has_pixi, has_uv

    excluded = set(exclude)
    dependencies: Dependencies = get_dependencies()
    has_at_least_one_update = False
    for dep_type in dependencies:
        if not len(dependencies[dep_type]):
            continue
        click.echo(f"- {dep_type} package(s):")
        # category = extras or group name
        for category, deps in dependencies[dep_type].items():
            if dep_type in ["dependencies", "build-system"]:
                category_name = ""
            elif dep_type == "optional-dependencies":
                category_name = f"extras: {category}"
            elif dep_type == "dependency-groups":
                category_name = f"group: {category}"
            else:
                raise ValueError(f"Invalid dependency type: {dep_type}")
            for dep in deps:
                msg = f"  {dep.requirement.name}: {dep.min_version}"
                has_update = dep.min_version != dep.latest_version
                is_excluded = dep.requirement.name in excluded
                if has_update:
                    if not is_excluded:
                        has_at_least_one_update = True
                    msg += (
                        f" → {click.style(dep.latest_version, fg='green', bold=True)}"
                    )
                if is_excluded:
                    msg += f" {click.style('(excluded)', fg='yellow')}"
                if category_name:
                    msg += f" ({category_name})"
                click.echo(msg)
    if not has_at_least_one_update:
        click.echo(f"\n{click.style('No dependencies to update.', bold=True)}")
        return
    if has_at_least_one_update and upgrade:
        if excluded:
            for dep_type in dependencies:
                for category, deps in dependencies[dep_type].items():
                    dependencies[dep_type][category] = [
                        dep._replace(latest_version=dep.min_version)
                        if dep.requirement.name in excluded
                        else dep
                        for dep in deps
                    ]
        update_dependencies(dependencies)  # write the latest versions to pyproject.toml
        if has_uv():
            click.echo("Upgrading dependencies with uv...")
            result = subprocess.run(["uv", "lock"], check=False)
            if result.returncode != 0:
                raise Exit(result.returncode)
            result = subprocess.run(
                ["uv", "sync", "--all-extras", "--all-groups"], check=False
            )
            if result.returncode != 0:
                raise Exit(result.returncode)
            click.echo(
                click.style(
                    "✓ All dependencies in pyproject.toml upgraded successfully 🎉",
                    fg="green",
                    bold=True,
                )
            )
        else:
            click.echo(
                "uv not found. Updated pyproject.toml only (packages not installed)."
            )
    if upgrade and all_:
        subprocess.run(["ap", "pre-commit", "autoupdate"])
        click.echo("All pre-commit hooks updated successfully.")
        if has_pixi():
            click.echo("Upgrading dependencies with pixi...")
            pixi_exclude_args = ["--exclude", "python"]
            for pkg in excluded:
                pixi_exclude_args += ["--exclude", pkg]
            result = subprocess.run(
                ["pixi", "upgrade", *pixi_exclude_args], check=False
            )
            if result.returncode != 0:
                raise Exit(result.returncode)
            result = subprocess.run(["pixi", "lock"], check=False)
            if result.returncode != 0:
                raise Exit(result.returncode)
            result = subprocess.run(["pixi", "install"], check=False)
            if result.returncode != 0:
                raise Exit(result.returncode)
            click.echo(
                click.style(
                    "✓ All dependencies in pixi.toml upgraded successfully 🎉",
                    fg="green",
                    bold=True,
                )
            )


update.add_command(dependencies, name="deps")  # alias for "dependencies"


@update.command()
@click.option("--deploy", is_flag=True, help="Update .github/workflows/deploy.yml")
@click.option("--ci", is_flag=True, help="Update .github/workflows/ci.yml")
@click.option("--release", is_flag=True, help="Update .github/workflows/release.yml")
@click.option("--dependabot", is_flag=True, help="Update .github/dependabot.yml")
@click.option(
    "--all",
    "all_",
    is_flag=True,
    help="Update every supported workflow file",
)
@click.option(
    "--no-backup",
    is_flag=True,
    help="Skip creating .backup copies of existing workflow files",
)
def workflows(
    deploy: bool,
    ci: bool,
    release: bool,
    dependabot: bool,
    all_: bool,
    no_backup: bool,
):
    """Update GitHub Actions workflow files (deploy, ci, release, dependabot)

    Existing files are backed up to <file>.backup before being overwritten
    so user customizations (matrix tweaks, extra steps, etc.) aren't lost.
    """
    from afterpython.tools.github_actions import (
        VALID_WORKFLOWS,
        update_workflow_file,
    )

    selected_flags = {
        "deploy": deploy,
        "ci": ci,
        "release": release,
        "dependabot": dependabot,
    }
    individual = [name for name, picked in selected_flags.items() if picked]

    if all_ and individual:
        raise click.UsageError("Pass --all or individual workflow flags, not both.")
    if not all_ and not individual:
        raise click.UsageError(
            "Specify which workflows to update with flags "
            "(e.g. --deploy --ci) or pass --all."
        )

    selected = VALID_WORKFLOWS if all_ else individual
    for name in selected:
        update_workflow_file(name, backup=not no_backup)


@update.command()
@click.pass_context
@click.option(
    "--no-backup",
    is_flag=True,
    help="Skip creating a backup of the existing website template",
)
def website(ctx, no_backup: bool):
    """Update project website template to the latest version"""
    from afterpython.utils import ensure_website_gitignore_rules, find_node_env

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
        result = subprocess.run(
            ["pnpx", "degit", website_template_repo, str(website_path)],
            env=node_env,
            check=False,
        )
        if result.returncode != 0:
            raise Exit(result.returncode)
        result = subprocess.run(
            ["pnpm", "install"], cwd=website_path, env=node_env, check=False
        )
        if result.returncode != 0:
            raise Exit(result.returncode)

        # Ensure gitignore rules are present
        ensure_website_gitignore_rules()
    except Exception as e:
        click.echo(f"✗ Error updating project website template: {e}", err=True)
        # On a fresh `ap init`, website_path didn't exist beforehand, so no backup
        # was created — skip restore in that case rather than crashing with
        # FileNotFoundError, which would mask the real error above.
        if not no_backup and backup_path.exists():
            click.echo("Restoring from backup...")
            if website_path.exists():
                shutil.rmtree(website_path)
            shutil.copytree(backup_path, website_path)
        raise
