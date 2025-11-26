import subprocess

import click
from click.exceptions import Exit

from afterpython.utils import has_pixi


@click.command(
    add_help_option=False,  # disable click's --help option so that cz --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
@click.option(
    "--pre",
    is_flag=True,
    help="bump to pre-release version (e.g., dev3 -> rc0, a1 -> a2)",
)
@click.option(
    "--release", is_flag=True, help="bump to stable release (uses cz bump default)"
)
def bump(ctx, release: bool, pre: bool):
    """Bump project version with granular control.

    By default, stays within current release phase:
    - Dev releases (e.g., 0.1.0.dev3) -> increment dev number (0.1.0.dev4)
    - Pre-releases (e.g., 0.1.0a1) -> increment pre-release (0.1.0a2)

    Use --pre to transition from dev to pre-release, or pre-release to next pre-release.
    Use --release to bump to next stable version (cz bump default behavior).
    """
    from afterpython.tools.pyproject import read_metadata
    from afterpython.utils import handle_passthrough_help

    # Show both our options and commitizen's help and exit
    handle_passthrough_help(
        ctx,
        ["cz", "bump"],
        show_underlying=True,
    )

    if release and pre:
        raise click.ClickException("Only one of --release or --pre can be specified")

    # bump using cz bump's default behavior
    if release:
        subprocess.run(["ap", "cz", "bump", *ctx.args])

        # Skip tag push if this is a dry run
        if "--dry-run" in ctx.args:
            return

        # Get the new version after bump
        metadata = read_metadata()
        new_version = metadata.version
        if new_version is None:
            raise click.ClickException("Unable to read version after bump")

        tag = f"v{new_version}"

        # Auto-push the specific tag to trigger release workflow
        click.echo(f"\n🚀 Pushing tag {tag} to trigger release workflow...")
        subprocess.run(["git", "push", "origin", tag])
    else:
        metadata = read_metadata()
        version = metadata.version

        if version is None:
            raise click.ClickException("Unable to read version from pyproject.toml")

        args = ctx.args  # default: pass through all extra args

        # by default, bump dev-release version
        if version.is_devrelease and not pre:
            devrelease_number = int(version.dev)
            if "--devrelease" not in ctx.args:
                args = ["--devrelease", str(devrelease_number + 1), *ctx.args]
        # exclude e.g. 0.1.0.dev1 which is both dev-release and pre-release (with version.pre = None)
        elif version.is_prerelease:
            prerelease_type = version.pre[0] if version.pre is not None else "rc"
            if prerelease_type == "a":
                prerelease_type = "alpha"
            elif prerelease_type == "b":
                prerelease_type = "beta"
            if "--prerelease" not in ctx.args:
                args = ["--prerelease", prerelease_type, *ctx.args]

        subprocess.run(["ap", "cz", "bump", *args])

    # Update pixi.lock after version bump (editable install requires lock refresh)
    if has_pixi():
        result = subprocess.run(["pixi", "install"], check=False)
        if result.returncode != 0:
            raise Exit(result.returncode)

        # Check if pixi.lock was modified
        status = subprocess.run(
            ["git", "diff", "--name-only", "pixi.lock"],
            capture_output=True,
            text=True,
            check=False,
        )
        if status.stdout.strip():
            # Stage and commit pixi.lock
            subprocess.run(["git", "add", "pixi.lock"], check=True)
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "build: update pixi.lock after version bump",
                ],
                check=True,
            )
            click.echo("✓ Committed pixi.lock update")
