import shutil
from pathlib import Path

import click

import afterpython as ap


def _copy_github_template(template_name: str, target_path: Path):
    """Helper to copy GitHub-related templates"""
    if target_path.exists():
        click.echo(f"{target_path} already exists")
        return

    # Create parent directory if it doesn't exist
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy template from package
    template_path = ap.paths.templates_path / template_name
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template file not found: {template_path}\n"
            "This might indicate a corrupted installation. Please reinstall afterpython."
        )

    shutil.copy(template_path, target_path)
    click.echo(f"Created {target_path}")


def create_workflow(workflow_name: str):
    """Create a GitHub Actions workflow from template"""
    if ".yml" in workflow_name:
        workflow_name = workflow_name.replace(".yml", "")

    user_path = ap.paths.user_path
    workflow_path = user_path / ".github" / "workflows" / f"{workflow_name}.yml"
    template_name = f"{workflow_name}-workflow-template.yml"

    _copy_github_template(template_name, workflow_path)


def create_dependabot():
    """Create Dependabot configuration for GitHub Actions updates"""
    user_path = ap.paths.user_path
    dependabot_path = user_path / ".github" / "dependabot.yml"
    template_name = "dependabot-template.yml"

    _copy_github_template(template_name, dependabot_path)
