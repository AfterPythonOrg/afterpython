import shutil
import subprocess

import click

import afterpython as ap


def init_ruff_toml():
    from afterpython.tools.pre_commit import update_pre_commit

    afterpython_path = ap.paths.afterpython_path
    ruff_toml_path = afterpython_path / "ruff.toml"
    if ruff_toml_path.exists():
        click.echo(f"Ruff configuration file {ruff_toml_path} already exists")
        return
    ruff_template_path = ap.paths.templates_path / "ruff-template.toml"
    shutil.copy(ruff_template_path, ruff_toml_path)
    click.echo(f"Created {ruff_toml_path}")
    # add ruff-pre-commit hook to .pre-commit-config.yaml
    data_update = {
        "repos": [
            {
                "repo": "https://github.com/astral-sh/ruff-pre-commit",
                "rev": "v0.14.6",
                "hooks": [
                    {
                        "id": "ruff-check",
                        "stages": ["pre-commit"],
                        "args": ["--config", "./afterpython/ruff.toml"],
                    },
                    {
                        "id": "ruff-format",
                        "stages": ["pre-commit"],
                        "args": ["--config", "./afterpython/ruff.toml"],
                    },
                ],
            },
        ]
    }
    update_pre_commit(data_update)


def init_website():
    click.echo(f"Initializing project website template in {ap.paths.website_path}...")
    subprocess.run(["ap", "update", "website"])


@click.command()
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Automatically answer yes to all prompts",
)
@click.pass_context
def init(ctx, yes):
    """Initialize afterpython with MyST Markdown (by default) and project website template"""
    from afterpython.tools._afterpython import init_afterpython
    from afterpython.tools.commitizen import init_commitizen
    from afterpython.tools.github_actions import (
        create_dependabot,
        create_workflow,
    )
    from afterpython.tools.myst import init_myst
    from afterpython.tools.pre_commit import init_pre_commit
    from afterpython.tools.pyproject import init_pyproject

    paths = ctx.obj["paths"]
    click.echo("Initializing afterpython...")
    afterpython_path = paths.afterpython_path
    static_path = paths.static_path

    afterpython_path.mkdir(parents=True, exist_ok=True)
    static_path.mkdir(parents=True, exist_ok=True)
    afterpython_path.joinpath("afterpython.toml").touch()

    init_pyproject()

    init_afterpython()

    init_myst()

    # TODO: init faq.yml

    init_website()

    create_workflow("deploy")
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
