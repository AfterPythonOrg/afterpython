import shutil
import subprocess

import click

import afterpython as ap

# pyproject.toml's [tool.ruff] only points to afterpython/ruff.toml,
# so that running `ruff` directly (or via editors) also uses afterpython/ruff.toml
RUFF_EXTEND = "afterpython/ruff.toml"


def _find_ruff_config_conflicts() -> list[str]:
    """Find ruff configs at the project root that would compete with afterpython/ruff.toml."""
    from afterpython.tools.pyproject import read_pyproject

    conflicts = [
        name
        for name in ("ruff.toml", ".ruff.toml")
        if (ap.paths.user_path / name).exists()
    ]
    tool_ruff = read_pyproject().get("tool", {}).get("ruff")
    if tool_ruff is not None and tool_ruff.unwrap() != {"extend": RUFF_EXTEND}:
        conflicts.append("[tool.ruff] in pyproject.toml")
    return conflicts


def init_ruff() -> str | None:
    """Returns a skip notice when an existing config made it skip the setup, else None."""
    import tomlkit

    from afterpython.tools.pyproject import read_pyproject, write_pyproject

    if conflicts := _find_ruff_config_conflicts():
        return (
            click.style(
                f"Skipped ruff setup: found existing ruff config ({', '.join(conflicts)}).\n",
                fg="yellow",
                bold=True,
            )
            + "afterpython keeps all ruff settings in afterpython/ruff.toml, "
            "and pyproject.toml's [tool.ruff] only points to it.\n"
            "Until then, `ap lint` and `ap format` will use your existing ruff config, "
            "not afterpython's, and there are no ruff hooks or CI lint job "
            "(set them up yourself if you want them).\n"
            "To fix: remove the config(s) above (keep a copy of any settings you want), "
            "run `ap init ruff`, then add your settings to afterpython/ruff.toml."
        )

    ruff_toml_path = ap.paths.afterpython_path / "ruff.toml"
    if ruff_toml_path.exists():
        click.echo(f"Ruff configuration file {ruff_toml_path} already exists")
    else:
        ruff_template_path = ap.paths.templates_path / "ruff-template.toml"
        shutil.copy(ruff_template_path, ruff_toml_path)
        click.echo(f"Created {ruff_toml_path}")

    data = read_pyproject()
    if "ruff" in data.get("tool", {}):
        return None  # already points to afterpython/ruff.toml (checked above)
    if "tool" not in data:
        data["tool"] = tomlkit.table(is_super_table=True)
    ruff_table = tomlkit.table()
    ruff_table["extend"] = RUFF_EXTEND
    data["tool"]["ruff"] = ruff_table
    write_pyproject(data)
    click.echo(f'Added [tool.ruff] extend = "{RUFF_EXTEND}" to pyproject.toml')
    return None


def _find_ty_config_conflicts() -> list[str]:
    """Find ty configs at the project root that `ap check` would silently ignore
    (it passes --config-file afterpython/ty.toml), while editors and plain `ty` still use them."""
    from afterpython.tools.pyproject import read_pyproject

    conflicts = []
    if (ap.paths.user_path / "ty.toml").exists():
        conflicts.append("ty.toml")
    if "ty" in read_pyproject().get("tool", {}):
        conflicts.append("[tool.ty] in pyproject.toml")
    return conflicts


def init_ty() -> str | None:
    """Returns a skip notice when an existing config made it skip the setup, else None."""
    if conflicts := _find_ty_config_conflicts():
        return (
            click.style(
                f"Skipped ty setup: found existing ty config ({', '.join(conflicts)}).\n",
                fg="yellow",
                bold=True,
            )
            + "afterpython keeps all ty settings in afterpython/ty.toml, "
            "which `ap check` passes to ty with --config-file.\n"
            "Until then, `ap check` will use your existing ty config, "
            "and there is no ty hook or CI type check job "
            "(set them up yourself if you want them).\n"
            "To fix: remove the config(s) above (keep a copy of any settings you want), "
            "run `ap init ty`, then add your settings to afterpython/ty.toml."
        )

    ty_toml_path = ap.paths.afterpython_path / "ty.toml"
    if ty_toml_path.exists():
        click.echo(f"ty configuration file {ty_toml_path} already exists")
        return None
    shutil.copy(ap.paths.templates_path / "ty-template.toml", ty_toml_path)
    click.echo(f"Created {ty_toml_path}")
    return None


def _find_cliff_config_conflicts() -> list[str]:
    """Find git-cliff configs at the project root that afterpython would silently ignore
    (it passes --config afterpython/cliff.toml), while plain `git cliff` still uses them."""
    from afterpython.tools.pyproject import read_pyproject

    conflicts = []
    if (ap.paths.user_path / "cliff.toml").exists():
        conflicts.append("cliff.toml")
    if "git-cliff" in read_pyproject().get("tool", {}):
        conflicts.append("[tool.git-cliff] in pyproject.toml")
    return conflicts


def init_cliff() -> str | None:
    """Returns a skip notice when an existing config made it skip the setup, else None."""
    if conflicts := _find_cliff_config_conflicts():
        return (
            click.style(
                f"Skipped git-cliff setup: found existing git-cliff config ({', '.join(conflicts)}).\n",
                fg="yellow",
                bold=True,
            )
            + "afterpython keeps all git-cliff settings in afterpython/cliff.toml, "
            "which it passes to git-cliff with --config.\n"
            "To fix: remove the config(s) above (keep a copy of any settings you want), "
            "run `ap init cliff`, then add your settings to afterpython/cliff.toml."
        )

    cliff_toml_path = ap.paths.afterpython_path / "cliff.toml"
    if cliff_toml_path.exists():
        click.echo(f"git-cliff configuration file {cliff_toml_path} already exists")
        return None
    shutil.copy(ap.paths.templates_path / "cliff-template.toml", cliff_toml_path)
    click.echo(f"Created {cliff_toml_path}")
    return None


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


def _preflight_init(website: bool) -> None:
    """Validate external prerequisites before any filesystem writes, so a
    failure aborts cleanly instead of leaving a half-initialized project."""
    if website:
        from afterpython.tools.myst import ensure_pnpm_12
        from afterpython.utils import find_node_env

        ensure_pnpm_12(find_node_env())


def _select_steps(yes: bool, skip_website: bool, ask_commit_types: bool) -> set[str]:
    """Ask which optional setup steps to run, as one checkbox list (all checked by default).

    Without a terminal (CI, piped input) or with --yes, nothing is asked and the defaults are used.
    """
    import sys

    import questionary

    # (step, label, checked by default)
    options = [
        (
            "website",
            "Project website (MyST, template, deploy workflow)",
            not skip_website,
        )
    ]
    # only relevant when afterpython.toml is created, it's ignored otherwise
    if ask_commit_types:
        options.append(
            (
                "commit_types",
                "Commit message check (conventional commit types, e.g. 'feat: add X')",
                True,
            )
        )
    options += [
        ("prek", "Pre-commit hooks (prek)", True),
        ("ruff", "ruff: lint & format", True),
        ("ty", "ty: type checking (`ap check`)", True),
        ("cliff", "git-cliff: changelog", True),
        ("release", "Release workflow (.github/workflows/release.yml)", True),
        ("dependabot", "Dependabot (auto-update GitHub Actions versions)", True),
    ]

    if yes or not (sys.stdin.isatty() and sys.stdout.isatty()):
        return {step for step, _, checked in options if checked}

    choices = [
        questionary.Choice(label, value=step, checked=checked)
        for step, label, checked in options
    ]
    selected = questionary.checkbox("Select what to set up", choices=choices).ask()
    if selected is None:  # Ctrl-C, before anything was written
        raise click.Abort()
    return set(selected)


@click.group(invoke_without_command=True)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Set up everything without asking",
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
    from afterpython.tools.github_actions import (
        create_dependabot,
        create_workflow,
    )
    from afterpython.tools.prek import init_prek, sync_hooks
    from afterpython.tools.pyproject import init_pyproject

    paths = ctx.obj["paths"]
    afterpython_path = paths.afterpython_path
    static_path = paths.static_path

    steps = _select_steps(
        yes,
        skip_website,
        ask_commit_types=not (afterpython_path / "afterpython.toml").exists(),
    )
    _preflight_init(website="website" in steps)

    click.echo("Initializing afterpython...")
    # printed after everything else, so they're in the last lines of the (long) output
    skip_notices: list[str] = []
    try:
        afterpython_path.mkdir(parents=True, exist_ok=True)
        static_path.mkdir(parents=True, exist_ok=True)

        init_pyproject()

        init_afterpython(commit_types="commit_types" in steps)

        if "website" in steps:
            # check=True so a failure inside `ap init website` aborts the parent
            # run instead of silently continuing to write more files.
            subprocess.run(["ap", "init", "website"], check=True)

        init_py_typed()

        create_workflow("ci")

        if "prek" in steps:
            init_prek()
        if "ruff" in steps and (notice := init_ruff()):
            skip_notices.append(notice)
        if "ty" in steps and (notice := init_ty()):
            skip_notices.append(notice)
        # whatever was selected: keep ruff/ty hooks only for the tools that were set up
        sync_hooks()

        if "cliff" in steps and (notice := init_cliff()):
            skip_notices.append(notice)
        if "release" in steps:
            create_workflow("release")
        if "dependabot" in steps:
            create_dependabot()
    except BaseException:
        if afterpython_path.exists():
            click.echo(f"ap init failed — removing {afterpython_path}", err=True)
            shutil.rmtree(afterpython_path, ignore_errors=True)
        raise

    for notice in skip_notices:
        click.echo()
        click.echo(notice)


@init.command("ruff")
def init_ruff_subcommand():
    """Initialize ruff config (afterpython/ruff.toml + [tool.ruff] in pyproject.toml)

    Use this to re-run the ruff setup, e.g. after removing a conflicting
    ruff config that made `ap init` skip it.
    """
    from afterpython.tools.prek import sync_hooks

    if notice := init_ruff():
        click.echo(notice)
    sync_hooks()


@init.command("ty")
def init_ty_subcommand():
    """Initialize ty config (afterpython/ty.toml, used by `ap check`)

    Use this to re-run the ty setup, e.g. after removing a conflicting
    ty config that made `ap init` skip it.
    """
    from afterpython.tools.prek import sync_hooks

    if notice := init_ty():
        click.echo(notice)
    sync_hooks()


@init.command("cliff")
def init_cliff_subcommand():
    """Initialize git-cliff config (afterpython/cliff.toml, used for changelog generation)

    Use this to re-run the git-cliff setup, e.g. after removing a conflicting
    git-cliff config that made `ap init` skip it.
    """
    if notice := init_cliff():
        click.echo(notice)


@init.command("website")
def init_website_subcommand():
    """Initialize project website (MyST config, template, deploy workflow)

    Use this if you ran `ap init --skip-website` and now want to add
    the website to an existing AfterPython project.
    """
    from afterpython.tools.github_actions import create_workflow
    from afterpython.tools.myst import ensure_pnpm_12, init_myst
    from afterpython.utils import find_node_env

    # Pre-flight: same rationale as `ap init` — guard the standalone entry too,
    # since this subcommand can be invoked directly via `ap init website`.
    ensure_pnpm_12(find_node_env())

    init_faq()
    init_myst()
    click.echo(f"Initializing project website template in {ap.paths.website_path}...")
    # check=True so a network/pnpm failure inside `ap update website` aborts
    # the subcommand instead of silently dropping the deploy workflow on top
    # of a broken website install.
    subprocess.run(["ap", "update", "website"], check=True)
    create_workflow("deploy")


@init.command("content")
@click.option("--all", is_flag=True, help="Initialize all content types")
@click.option("--doc", is_flag=True, help="Initialize afterpython/doc/")
@click.option("--blog", is_flag=True, help="Initialize afterpython/blog/")
@click.option("--tutorial", is_flag=True, help="Initialize afterpython/tutorial/")
@click.option("--example", is_flag=True, help="Initialize afterpython/example/")
@click.option("--guide", is_flag=True, help="Initialize afterpython/guide/")
def init_content_subcommand(
    all: bool, doc: bool, blog: bool, tutorial: bool, example: bool, guide: bool
):
    """Initialize content directories (MyST config) without touching the website

    Content types that already have a myst.yml are skipped.

    Examples:
      ap init content --blog             # afterpython/blog/
      ap init content --blog --tutorial  # afterpython/blog/ and afterpython/tutorial/
      ap init content --all              # every content type that is missing
    """
    from afterpython._typing import tContentType
    from afterpython.const import CONTENT_TYPES
    from afterpython.tools.myst import init_myst

    flags: dict[tContentType, bool] = {
        "doc": doc,
        "blog": blog,
        "tutorial": tutorial,
        "example": example,
        "guide": guide,
    }
    if all:
        content_types = CONTENT_TYPES
    else:
        content_types = {content_type for content_type, flag in flags.items() if flag}
    if not content_types:
        raise click.UsageError(
            "Specify one or more of --doc/--blog/--tutorial/--example/--guide, or --all"
        )
    init_myst(content_types)
