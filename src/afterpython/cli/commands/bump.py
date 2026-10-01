import os
import subprocess
import sys

import click
from packaging.version import Version

# uv's --bump names for PEP 440 pre-release markers
PRE_KINDS = {"a": "alpha", "b": "beta", "rc": "rc"}
CHANGELOG = "CHANGELOG.md"
# git-cliff ignores pre-release and dev tags (e.g. v0.4.0rc1, v0.4.0.dev2),
# so a stable release's section has every commit since the previous stable release
PRE_RELEASE_TAGS = "(a|b|rc|dev)[0-9]+"


def _uv_version_args(
    version: Version, release: bool, pre: bool, level: str
) -> list[str]:
    """Arguments for `uv version`, either `--bump ...` or an exact version"""
    is_stable = not version.is_prerelease  # dev versions count as pre-releases too
    if not is_stable and level != "patch":
        raise click.ClickException(
            f"--{level} only applies to stable versions, current version is {version}"
        )
    if release:
        # e.g. 0.1.0rc0 -> 0.1.0, 0.3.19 -> 0.3.20
        return ["--bump", "stable" if not is_stable else level]
    if is_stable:
        # e.g. 0.3.19 -> 0.3.20 (or 0.3.20rc0 with --pre)
        return ["--bump", level, *(["--bump", "rc=0"] if pre else [])]
    if version.is_devrelease:
        if not pre:
            # e.g. 0.1.0.dev3 -> 0.1.0.dev4
            return ["--bump", "dev"]
        if version.pre is None:
            # e.g. 0.1.0.dev3 -> 0.1.0rc0
            return ["--bump", "rc=0"]
        # e.g. 0.1.0rc0.dev2 -> 0.1.0rc0 (uv's --bump rc would skip to rc1)
        kind, number = version.pre
        return [str(Version(f"{version.base_version}{kind}{number}"))]
    # e.g. 0.1.0a1 -> 0.1.0a2, 0.1.0rc0 -> 0.1.0rc1
    assert version.pre is not None  # not stable and not dev, so it's a pre-release
    return ["--bump", PRE_KINDS[version.pre[0]]]


def _git(*args: str) -> subprocess.CompletedProcess:
    import afterpython as ap

    return subprocess.run(
        ["git", *args],
        cwd=ap.paths.user_path,
        capture_output=True,
        text=True,
        check=False,
    )


def _restore(files: list[str], new_files: list[str]):
    """Undo the version bump in the working tree and index"""
    import afterpython as ap

    _git("restore", "--source=HEAD", "--staged", "--worktree", "--", *files)
    for file in new_files:
        _git("rm", "--cached", "--quiet", "--ignore-unmatch", "--", file)
        (ap.paths.user_path / file).unlink(missing_ok=True)
    click.echo(f"↩️  Restored {', '.join(files + new_files)}", err=True)


def _write_changelog(tag: str):
    """Write the release section for tag to CHANGELOG.md with git-cliff"""
    import afterpython as ap

    cmd = [
        "git-cliff",
        "--config",
        str(ap.paths.afterpython_path / "cliff.toml"),
        "--tag",
        tag,
        "--ignore-tags",
        PRE_RELEASE_TAGS,
    ]
    if (ap.paths.user_path / CHANGELOG).exists():
        # only add the new section on top, keeping manual edits to older ones;
        # a range from the previous stable tag, since --unreleased would drop
        # the commits before an ignored pre-release tag (e.g. v0.4.1rc0)
        previous = _git(
            "describe",
            "--tags",
            "--abbrev=0",
            "--match",
            "v*",
            *(f"--exclude=*{kind}[0-9]*" for kind in ("a", "b", "rc", "dev")),
        ).stdout.strip()
        cmd += [f"{previous}..HEAD" if previous else "--unreleased"]
        cmd += ["--prepend", CHANGELOG]
    else:
        # git-cliff can't prepend to a missing file, so create it from the full history
        cmd += ["--output", CHANGELOG]
    result = subprocess.run(
        cmd, cwd=ap.paths.user_path, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise click.ClickException(f"git-cliff failed:\n{result.stderr.strip()}")


def _is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _edit_changelog():
    """Open CHANGELOG.md in git's editor, the bump continues once it's closed"""
    import afterpython as ap

    result = _git("var", "GIT_EDITOR")
    if result.returncode != 0:
        raise click.ClickException(
            f"Failed to find git's editor:\n{result.stderr.strip()}"
        )
    editor = result.stdout.strip()
    click.echo(
        f"✏️  Opening {CHANGELOG} in {editor}, save and close it to commit the bump "
        "(to abort, press Ctrl+C or exit the editor with an error, e.g. :cq in vim)"
    )
    # raises ClickException if the editor exits with an error, which rolls back the bump
    click.edit(filename=str(ap.paths.user_path / CHANGELOG), editor=editor)


@click.command()
@click.option(
    "--pre",
    is_flag=True,
    help="bump to pre-release version (e.g., 0.1.0.dev3 -> 0.1.0rc0, 0.1.0a1 -> 0.1.0a2)",
)
@click.option(
    "--release",
    is_flag=True,
    help="bump to stable version (e.g., 0.1.0rc0 -> 0.1.0, 0.3.19 -> 0.3.20) and push it with its tag to trigger the release workflow (default branch only)",
)
@click.option(
    "--minor",
    is_flag=True,
    help="bump the minor version instead of patch (stable versions only, e.g., 0.3.19 -> 0.4.0)",
)
@click.option(
    "--major",
    is_flag=True,
    help="bump the major version instead of patch (stable versions only, e.g., 0.3.19 -> 1.0.0)",
)
@click.option(
    "--no-edit",
    is_flag=True,
    help="don't open CHANGELOG.md in git's editor before committing a stable bump",
)
@click.option(
    "--dry-run", is_flag=True, help="show the new version without changing anything"
)
def bump(
    release: bool, pre: bool, minor: bool, major: bool, no_edit: bool, dry_run: bool
):
    """Bump project version, commit it and tag it.

    \b
    By default, stays within current release phase:
    - Dev releases (e.g., 0.1.0.dev3) -> increment dev number (0.1.0.dev4)
    - Pre-releases (e.g., 0.1.0a1) -> increment pre-release (0.1.0a2)
    - Stable releases (e.g., 0.3.19) -> increment patch (0.3.20), or --minor/--major

    Use --pre to transition from dev to pre-release, or pre-release to next pre-release.
    Stable bumps also add the new release section to CHANGELOG.md with git-cliff
    (if afterpython/cliff.toml exists, see `ap init cliff`) and open it in git's editor,
    the bump is committed once you close it (use --no-edit to skip).
    Use --release to bump to a stable version and push it with its tag (triggers the release workflow),
    only allowed on the default branch (e.g. main).
    """
    import afterpython as ap
    from afterpython.tools._git import check_release_branch
    from afterpython.tools.pyproject import read_metadata
    from afterpython.utils import has_pixi

    if release and pre:
        raise click.ClickException("Only one of --release or --pre can be specified")
    if minor and major:
        raise click.ClickException("Only one of --minor or --major can be specified")
    level = "minor" if minor else "major" if major else "patch"

    # before changing anything, so a wrong branch doesn't leave a bump behind
    if release:
        check_release_branch()

    version = read_metadata().version
    if version is None:
        raise click.ClickException("Unable to read version from pyproject.toml")
    uv_args = _uv_version_args(version, release, pre, level)

    user_path = ap.paths.user_path
    # without uv.lock, --frozen stops uv from creating one; with it, uv updates it
    has_uv_lock = (user_path / "uv.lock").exists()
    uv_lock_arg = "--no-sync" if has_uv_lock else "--frozen"
    result = subprocess.run(
        ["uv", "version", *uv_args, "--dry-run", "--short", "--frozen"],
        cwd=user_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise click.ClickException(result.stderr.strip())
    new_version = result.stdout.strip()
    tag = f"v{new_version}"

    uses_pixi = (user_path / "pixi.lock").exists()
    if uses_pixi and not has_pixi():
        click.echo("⚠️  pixi.lock found but pixi is not installed, skip updating it")
        uses_pixi = False
    candidates = [
        "pyproject.toml",
        *(["uv.lock"] if has_uv_lock else []),
        *(["pixi.lock"] if uses_pixi else []),
    ]
    # only stable bumps write the changelog, and only when afterpython/cliff.toml was set up
    writes_changelog = (
        not Version(new_version).is_prerelease
        and (ap.paths.afterpython_path / "cliff.toml").exists()
    )
    if writes_changelog:
        candidates.append(CHANGELOG)
    # no editor in CI or tests
    edits_changelog = writes_changelog and not no_edit and _is_interactive()
    files = _git("ls-files", "--", *candidates).stdout.split()
    if "pyproject.toml" not in files:
        raise click.ClickException("pyproject.toml is not tracked by git")
    # CHANGELOG.md created by this bump, removed again if the bump fails
    new_files: list[str] = []
    if writes_changelog and CHANGELOG not in files:
        if (user_path / CHANGELOG).exists():
            raise click.ClickException(
                f"{CHANGELOG} exists but is not tracked by git, commit or remove it first"
            )
        new_files.append(CHANGELOG)

    # the bump commit only contains the version change
    dirty = _git("status", "--porcelain", "--", *files).stdout.strip()
    if dirty:
        raise click.ClickException(
            f"Commit or stash your changes to these files first:\n{dirty}"
        )
    if _git("rev-parse", "--quiet", "--verify", f"refs/tags/{tag}").returncode == 0:
        raise click.ClickException(f"Tag {tag} already exists")
    # otherwise uv would re-lock other packages into the bump commit
    if has_uv_lock and (
        subprocess.run(
            ["uv", "lock", "--check"], cwd=user_path, capture_output=True, check=False
        ).returncode
        != 0
    ):
        raise click.ClickException(
            "uv.lock is out of date, run `uv lock` and commit it first"
        )

    if dry_run:
        click.echo(f"{version} → {new_version}")
        if writes_changelog:
            click.echo(f"Would write the {new_version} section to {CHANGELOG}")
            if edits_changelog:
                click.echo(f"Would open {CHANGELOG} in git's editor before committing")
        click.echo(f"Would commit {', '.join(files + new_files)} and create tag {tag}")
        if release:
            click.echo(f"Would push the current branch and tag {tag} to origin")
        return

    try:
        result = subprocess.run(
            ["uv", "version", *uv_args, uv_lock_arg], cwd=user_path, check=False
        )
        if result.returncode != 0:
            raise click.ClickException("uv version failed")
        if read_metadata().version != Version(new_version):
            raise click.ClickException(
                f"Expected version {new_version} in pyproject.toml after the bump"
            )
        # refresh the pixi env; older pixi versions also record the editable version in pixi.lock
        if uses_pixi:
            result = subprocess.run(["pixi", "install"], cwd=user_path, check=False)
            if result.returncode != 0:
                raise click.ClickException("pixi install failed")
        if writes_changelog:
            _write_changelog(tag)
            click.echo(f"📝 Wrote the {new_version} section to {CHANGELOG}")
        if edits_changelog:
            _edit_changelog()
        if new_files:
            # `git commit -- <files>` only takes files git already knows about
            result = _git("add", "--", *new_files)
            if result.returncode != 0:
                raise click.ClickException(f"git add failed:\n{result.stderr.strip()}")

        # skip the commit message check, "bump" is not one of the commit types
        env = os.environ.copy()
        env["SKIP"] = ",".join(filter(None, [env.get("SKIP"), "ap-commit"]))
        message = f"bump: version {version} → {new_version}"
        # `git commit -- <files>` commits only these files, leaving anything else staged as is
        result = subprocess.run(
            ["git", "commit", "-m", message, "--", *files, *new_files],
            cwd=user_path,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            raise click.ClickException("git commit failed")
    except (click.ClickException, KeyboardInterrupt):
        _restore(files, new_files)
        raise

    result = _git("tag", tag)
    if result.returncode != 0:
        raise click.ClickException(
            f"Committed the bump but failed to create tag {tag}:\n{result.stderr.strip()}"
        )
    click.echo(f"✅ Bumped {version} → {new_version} and tagged {tag}")

    if release:
        # ap release pushes the branch and the tag, which triggers the release workflow
        click.echo()
        result = subprocess.run(["ap", "release"], cwd=user_path, check=False)
        if result.returncode != 0:
            raise click.ClickException(
                f"Bumped and tagged {tag} but didn't push it, retry with: ap release"
            )
