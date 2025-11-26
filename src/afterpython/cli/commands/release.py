import subprocess

import click


@click.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force release even for dev versions (not recommended)",
)
def release(force: bool):
    """Manually trigger a release by pushing the current version tag.

    This command is used to manually publish dev versions or pre-releases to PyPI
    and create GitHub releases. It pushes the tag for the current version, which
    triggers the GitHub Actions release workflow.

    By default, releases are only allowed for non-dev versions (stable releases
    and pre-releases like rc, alpha, beta). Use --force to release dev versions.

    The release workflow will:
    - Run tests in CI
    - Publish to PyPI (if tests pass)
    - Create a GitHub release (if tests pass)

    Examples:
        ap bump --pre      # Bump to pre-release (e.g., 0.1.0rc1)
        ap release         # Push tag → triggers release workflow

        ap bump            # Bump dev version (e.g., 0.1.0.dev4)
        ap release --force # Push tag → triggers release workflow (dev version)
    """
    from afterpython.tools.pyproject import read_metadata

    # Get current version from pyproject.toml
    metadata = read_metadata()
    version = metadata.version

    if version is None:
        raise click.ClickException("Unable to read version from pyproject.toml")

    # Check if this is a dev version
    if version.is_devrelease and not force:
        raise click.ClickException(
            f"Cannot release dev version '{version}' without --force flag.\n"
            f"Dev versions are typically not published to PyPI.\n"
            f"Use 'ap bump --release' for stable releases (auto-releases),\n"
            f"or 'ap bump --pre' then 'ap release' for pre-releases,\n"
            f"or 'ap release --force' to release this dev version anyway."
        )

    tag = f"v{version}"

    click.echo(f"🏷️  Pushing tag {tag} to trigger release workflow...")
    result = subprocess.run(["git", "push", "origin", tag], capture_output=False)

    if result.returncode != 0:
        click.echo(f"\n❌ Failed to push tag (exit code {result.returncode})", err=True)
        raise click.ClickException("Git push failed")

    click.echo(f"✅ Tag {tag} pushed successfully")
    click.echo("\n📋 Check GitHub Actions to see the release workflow progress.")

    if version.is_devrelease:
        click.echo("   ⚠️  Warning: Publishing a dev version to PyPI and GitHub")
