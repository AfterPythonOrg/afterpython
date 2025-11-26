import shutil

import click

import afterpython as ap


def create_workflow(workflow_name: str):
    if ".yml" in workflow_name:
        workflow_name = workflow_name.replace(".yml", "")

    user_path = ap.paths.user_path
    workflow_dir = user_path / ".github" / "workflows"
    workflow_path = workflow_dir / f"{workflow_name}.yml"

    if workflow_path.exists():
        click.echo(
            f"GitHub Actions {workflow_name} workflow {workflow_path} already exists"
        )
        return

    # Create .github/workflows directory if it doesn't exist
    workflow_dir.mkdir(parents=True, exist_ok=True)

    # Copy template from package
    template_path = ap.paths.templates_path / f"{workflow_name}-workflow-template.yml"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template file not found: {template_path}\n"
            "This might indicate a corrupted installation. Please reinstall afterpython."
        )

    shutil.copy(template_path, workflow_path)
    click.echo(f"Created {workflow_path}")
