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
    """Manually trigger a release by pushing the current branch and version tag.

    This command is used to manually publish dev versions or pre-releases to PyPI
    and create GitHub releases. It pushes the current branch together with the tag
    for the current version, which triggers the GitHub Actions release workflow.
    Releases are only allowed from the default branch (e.g. main).

    By default, releases are only allowed for non-dev versions (stable releases
    and pre-releases like rc, alpha, beta). Use --force to release dev versions.

    The release workflow will:
    - Run the CI workflow (lint, tests, build)
    - Publish to PyPI (if CI passes)
    - Create a GitHub release (if CI passes)

    Examples:
        ap bump --pre      # Bump to pre-release (e.g., 0.1.0rc1)
        ap release         # Push tag → triggers release workflow

        ap bump            # Bump dev version (e.g., 0.1.0.dev4)
        ap release --force # Push tag → triggers release workflow (dev version)
    """
    import afterpython as ap
    from afterpython.tools._git import check_release_branch
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

    branch = check_release_branch()
    tag = f"v{version}"

    def git_ok(*args: str) -> bool:
        return (
            subprocess.run(
                ["git", *args], cwd=ap.paths.user_path, capture_output=True, check=False
            ).returncode
            == 0
        )

    if not git_ok("rev-parse", "--quiet", "--verify", f"refs/tags/{tag}"):
        raise click.ClickException(f"Tag {tag} not found, create it with 'ap bump'")
    # the released code must be on the branch that gets pushed with the tag
    if not git_ok("merge-base", "--is-ancestor", tag, "HEAD"):
        raise click.ClickException(
            f"Tag {tag} is not on branch '{branch}' (e.g. the bump commit was rebased), "
            f"move it to the bump commit with: git tag -f {tag} <commit>"
        )

    click.echo(f"🏷️  Pushing {branch} and tag {tag} to trigger release workflow...")
    # --atomic: either both are pushed or neither, so a release never misses its commits on GitHub
    result = subprocess.run(
        ["git", "push", "--atomic", "origin", branch, tag],
        cwd=ap.paths.user_path,
        check=False,
    )

    if result.returncode != 0:
        click.echo(
            f"\n❌ Failed to push {branch} and tag {tag} (exit code {result.returncode}), nothing was pushed",
            err=True,
        )
        raise click.ClickException("Git push failed")

    click.echo(f"✅ {branch} and tag {tag} pushed successfully")
    click.echo("\n📋 Check GitHub Actions to see the release workflow progress.")

    if version.is_devrelease:
        click.echo("   ⚠️  Warning: Publishing a dev version to PyPI and GitHub")
