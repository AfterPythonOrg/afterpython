# VIBE-CODED
import shutil
from pathlib import Path

import click

import afterpython as ap

# Workflow names supported by `create_workflow` / `update_workflow_file`.
# "dependabot" is included even though it lives at .github/dependabot.yml
# (not under workflows/) so a single CLI surface can refresh all GH templates.
VALID_WORKFLOWS = ("deploy", "ci", "release", "dependabot")


def _resolve_workflow_target(name: str) -> tuple[Path, Path]:
    """Return (target_path, template_path) for a workflow name."""
    if name not in VALID_WORKFLOWS:
        raise ValueError(
            f"Unknown workflow '{name}'. Valid: {', '.join(VALID_WORKFLOWS)}"
        )
    user_path = ap.paths.user_path
    templates_path = ap.paths.templates_path
    if name == "dependabot":
        target = user_path / ".github" / "dependabot.yml"
        template = templates_path / "dependabot-template.yml"
    else:
        target = user_path / ".github" / "workflows" / f"{name}.yml"
        template = templates_path / f"{name}-workflow-template.yml"
    return target, template


def _copy_github_template(template_path: Path, target_path: Path):
    """Copy a template file into the project, creating parent dirs as needed."""
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template file not found: {template_path}\n"
            "This might indicate a corrupted installation. Please reinstall afterpython."
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(template_path, target_path)


def create_workflow(workflow_name: str):
    """Create a GitHub Actions workflow from template (no-op if it exists)."""
    if ".yml" in workflow_name:
        workflow_name = workflow_name.replace(".yml", "")

    target_path, template_path = _resolve_workflow_target(workflow_name)
    if target_path.exists():
        click.echo(f"{target_path} already exists")
        return
    _copy_github_template(template_path, target_path)
    click.echo(f"Created {target_path}")


def create_dependabot():
    """Create Dependabot configuration for GitHub Actions updates."""
    target_path, template_path = _resolve_workflow_target("dependabot")
    if target_path.exists():
        click.echo(f"{target_path} already exists")
        return
    _copy_github_template(template_path, target_path)
    click.echo(f"Created {target_path}")


def update_workflow_file(name: str, backup: bool = True):
    """Overwrite a workflow file with the latest template.

    If the target already exists and ``backup`` is True, the existing file is
    copied to ``<file>.backup`` first so user customizations aren't lost.
    """
    target_path, template_path = _resolve_workflow_target(name)
    if target_path.exists():
        if backup:
            backup_path = Path(str(target_path) + ".backup")
            shutil.copy(target_path, backup_path)
            click.echo(f"Backed up {target_path} → {backup_path}")
        _copy_github_template(template_path, target_path)
        click.echo(f"Updated {target_path}")
    else:
        _copy_github_template(template_path, target_path)
        click.echo(f"Created {target_path}")
