import shutil
import subprocess

import click

import afterpython as ap


def init_ruff_toml():
    ruff_toml_path = ap.paths.afterpython_path / "ruff.toml"
    if ruff_toml_path.exists():
        click.echo(f"Ruff configuration file {ruff_toml_path} already exists")
        return
    ruff_template_path = ap.paths.templates_path / "ruff-template.toml"
    shutil.copy(ruff_template_path, ruff_toml_path)
    click.echo(f"Created {ruff_toml_path}")


def init_faq():
    faq_path = ap.paths.afterpython_path / "faq.yml"
    if faq_path.exists():
        click.echo(f"FAQ file already exists at {faq_path}")
        return
    faq_path.touch()
    click.echo(f"Created {faq_path}")


def init_py_typed():
    from afterpython.tools.pyproject import find_package_directory

    try:
        package_dir = find_package_directory()
    except FileNotFoundError:
        click.echo(
            "Could not find package directory (__init__.py not found), skipping py-typed initialization"
        )
        return
    py_typed_path = package_dir / "py.typed"
    if py_typed_path.exists():
        click.echo(f"py.typed file already exists at {py_typed_path}")
        return
    py_typed_path.touch()
    click.echo(f"Created {py_typed_path}")


@click.group(invoke_without_command=True)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Automatically answer yes to all prompts",
)
@click.option(
    "--skip-website",
    is_flag=True,
    help="Skip website template initialization (run `ap init website` later to add it)",
)
@click.pass_context
def init(ctx, yes, skip_website: bool):
    """Initialize AfterPython project structure and website template"""
    if ctx.invoked_subcommand is not None:
        return

    from afterpython.tools._afterpython import init_afterpython
    from afterpython.tools.commitizen import init_commitizen
    from afterpython.tools.github_actions import (
        create_dependabot,
        create_workflow,
    )
    from afterpython.tools.pre_commit import init_pre_commit
    from afterpython.tools.pyproject import init_pyproject

    paths = ctx.obj["paths"]
    click.echo("Initializing afterpython...")
    afterpython_path = paths.afterpython_path
    static_path = paths.static_path

    afterpython_path.mkdir(parents=True, exist_ok=True)
    static_path.mkdir(parents=True, exist_ok=True)

    init_pyproject()

    init_afterpython()

    if not skip_website:
        subprocess.run(["ap", "init", "website"])

    # TODO: add type checking related stuff here
    init_py_typed()

    create_workflow("ci")

    if yes or click.confirm(
        f"\nCreate .pre-commit-config.yaml in {afterpython_path}?", default=True
    ):
        init_pre_commit()

    if yes or click.confirm(f"\nCreate ruff.toml in {afterpython_path}?", default=True):
        init_ruff_toml()

    if yes or click.confirm(
        f"\nCreate commitizen configuration (cz.toml) in {afterpython_path} "
        f"and release workflow in .github/workflows/release.yml?",
        default=True,
    ):
        init_commitizen()
        create_workflow("release")

    if yes or click.confirm(
        "\nCreate Dependabot configuration (.github/dependabot.yml) "
        "to auto-update GitHub Actions versions?",
        default=True,
    ):
        create_dependabot()


@init.command("website")
def init_website_subcommand():
    """Initialize project website (MyST config, template, deploy workflow)

    Use this if you ran `ap init --skip-website` and now want to add
    the website to an existing AfterPython project.
    """
    from afterpython.tools.github_actions import create_workflow
    from afterpython.tools.myst import init_myst

    init_faq()
    init_myst()
    click.echo(f"Initializing project website template in {ap.paths.website_path}...")
    subprocess.run(["ap", "update", "website"])
    create_workflow("deploy")
