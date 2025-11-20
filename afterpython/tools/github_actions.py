import shutil

import click

import afterpython as ap


def init_release_workflow():
    """Initialize GitHub Actions release workflow.

    Creates .github/workflows/release.yml in the user's project root.
    This workflow triggers on version tags and:
    - Builds the package with uv
    - Publishes to PyPI using trusted publishing
    - Creates GitHub releases (with pre-release detection)
    """
    user_path = ap.paths.user_path
    workflow_dir = user_path / ".github" / "workflows"
    workflow_path = workflow_dir / "release.yml"

    if workflow_path.exists():
        click.echo(f"GitHub Actions release workflow {workflow_path} already exists")
        return

    # Create .github/workflows directory if it doesn't exist
    workflow_dir.mkdir(parents=True, exist_ok=True)

    # Copy template from package
    template_path = ap.paths.templates_path / "release-workflow-template.yml"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template file not found: {template_path}\n"
            "This might indicate a corrupted installation. Please reinstall afterpython."
        )

    shutil.copy(template_path, workflow_path)
    click.echo(f"Created {workflow_path}")
    click.echo(
        "\n📋 Next steps to enable releases:\n"
        "   1. Enable PyPI trusted publishing:\n"
        "      - Go to https://pypi.org/manage/account/publishing/\n"
        "      - Add your repository and workflow file: release.yml\n"
        "   2. Push tags to trigger releases:\n"
        "      - Use 'ap bump --release' for stable releases (auto-pushes tag)\n"
        "      - Use 'ap bump --pre' then 'ap release' for pre-releases\n"
    )
