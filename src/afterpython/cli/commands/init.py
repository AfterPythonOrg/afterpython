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


def init_ruff():
    import tomlkit

    from afterpython.tools.pyproject import read_pyproject, write_pyproject

    if conflicts := _find_ruff_config_conflicts():
        click.echo(
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
        return

    ruff_toml_path = ap.paths.afterpython_path / "ruff.toml"
    if ruff_toml_path.exists():
        click.echo(f"Ruff configuration file {ruff_toml_path} already exists")
    else:
        ruff_template_path = ap.paths.templates_path / "ruff-template.toml"
        shutil.copy(ruff_template_path, ruff_toml_path)
        click.echo(f"Created {ruff_toml_path}")

    data = read_pyproject()
    if "ruff" in data.get("tool", {}):
        return  # already points to afterpython/ruff.toml (checked above)
    if "tool" not in data:
        data["tool"] = tomlkit.table(is_super_table=True)
    ruff_table = tomlkit.table()
    ruff_table["extend"] = RUFF_EXTEND
    data["tool"]["ruff"] = ruff_table
    write_pyproject(data)
    click.echo(f'Added [tool.ruff] extend = "{RUFF_EXTEND}" to pyproject.toml')


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


def init_ty():
    if conflicts := _find_ty_config_conflicts():
        click.echo(
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
        return

    ty_toml_path = ap.paths.afterpython_path / "ty.toml"
    if ty_toml_path.exists():
        click.echo(f"ty configuration file {ty_toml_path} already exists")
        return
    shutil.copy(ap.paths.templates_path / "ty-template.toml", ty_toml_path)
    click.echo(f"Created {ty_toml_path}")


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


def init_cliff():
    if conflicts := _find_cliff_config_conflicts():
        click.echo(
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
        return

    cliff_toml_path = ap.paths.afterpython_path / "cliff.toml"
    if cliff_toml_path.exists():
        click.echo(f"git-cliff configuration file {cliff_toml_path} already exists")
        return
    shutil.copy(ap.paths.templates_path / "cliff-template.toml", cliff_toml_path)
    click.echo(f"Created {cliff_toml_path}")


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


def _preflight_init(skip_website: bool) -> None:
    """Validate external prerequisites before any filesystem writes, so a
    failure aborts cleanly instead of leaving a half-initialized project."""
    if not skip_website:
        from afterpython.tools.myst import ensure_pnpm_11
        from afterpython.utils import find_node_env

        ensure_pnpm_11(find_node_env())


@click.group(invoke_without_command=True)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Automatically answer yes to all prompts",
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

    _preflight_init(skip_website)

    paths = ctx.obj["paths"]
    click.echo("Initializing afterpython...")
    afterpython_path = paths.afterpython_path
    static_path = paths.static_path

    try:
        afterpython_path.mkdir(parents=True, exist_ok=True)
        static_path.mkdir(parents=True, exist_ok=True)

        init_pyproject()

        # only asked when afterpython.toml is created, it's ignored otherwise
        commit_types = (
            yes
            or (afterpython_path / "afterpython.toml").exists()
            or click.confirm(
                "\nCheck commit messages against conventional commit types "
                "(e.g. 'feat: add X', types listed in afterpython.toml)?",
                default=True,
            )
        )
        init_afterpython(commit_types=commit_types)

        if not skip_website:
            # check=True so a failure inside `ap init website` aborts the parent
            # run instead of silently continuing to write more files.
            subprocess.run(["ap", "init", "website"], check=True)

        init_py_typed()

        create_workflow("ci")

        if yes or click.confirm(
            f"\nCreate .pre-commit-config.yaml in {afterpython_path}?", default=True
        ):
            init_prek()

        if yes or click.confirm(
            f"\nCreate ruff.toml in {afterpython_path} (and point pyproject.toml's [tool.ruff] to it)?",
            default=True,
        ):
            init_ruff()

        if yes or click.confirm(
            f"\nCreate ty.toml in {afterpython_path} (type checking with `ap check`)?",
            default=True,
        ):
            init_ty()
        # whatever the answers: keep ruff/ty hooks only for the tools that were set up
        sync_hooks()

        if yes or click.confirm(
            f"\nCreate cliff.toml in {afterpython_path} (changelog generation with git-cliff)?",
            default=True,
        ):
            init_cliff()

        if yes or click.confirm(
            "\nCreate release workflow in .github/workflows/release.yml?",
            default=True,
        ):
            create_workflow("release")

        if yes or click.confirm(
            "\nCreate Dependabot configuration (.github/dependabot.yml) "
            "to auto-update GitHub Actions versions?",
            default=True,
        ):
            create_dependabot()
    except BaseException:
        if afterpython_path.exists():
            click.echo(f"ap init failed — removing {afterpython_path}", err=True)
            shutil.rmtree(afterpython_path, ignore_errors=True)
        raise


@init.command("ruff")
def init_ruff_subcommand():
    """Initialize ruff config (afterpython/ruff.toml + [tool.ruff] in pyproject.toml)

    Use this to re-run the ruff setup, e.g. after removing a conflicting
    ruff config that made `ap init` skip it.
    """
    from afterpython.tools.prek import sync_hooks

    init_ruff()
    sync_hooks()


@init.command("ty")
def init_ty_subcommand():
    """Initialize ty config (afterpython/ty.toml, used by `ap check`)

    Use this to re-run the ty setup, e.g. after removing a conflicting
    ty config that made `ap init` skip it.
    """
    from afterpython.tools.prek import sync_hooks

    init_ty()
    sync_hooks()


@init.command("cliff")
def init_cliff_subcommand():
    """Initialize git-cliff config (afterpython/cliff.toml, used for changelog generation)

    Use this to re-run the git-cliff setup, e.g. after removing a conflicting
    git-cliff config that made `ap init` skip it.
    """
    init_cliff()


@init.command("website")
def init_website_subcommand():
    """Initialize project website (MyST config, template, deploy workflow)

    Use this if you ran `ap init --skip-website` and now want to add
    the website to an existing AfterPython project.
    """
    from afterpython.tools.github_actions import create_workflow
    from afterpython.tools.myst import ensure_pnpm_11, init_myst
    from afterpython.utils import find_node_env

    # Pre-flight: same rationale as `ap init` — guard the standalone entry too,
    # since this subcommand can be invoked directly via `ap init website`.
    ensure_pnpm_11(find_node_env())

    init_faq()
    init_myst()
    click.echo(f"Initializing project website template in {ap.paths.website_path}...")
    # check=True so a network/pnpm failure inside `ap update website` aborts
    # the subcommand instead of silently dropping the deploy workflow on top
    # of a broken website install.
    subprocess.run(["ap", "update", "website"], check=True)
    create_workflow("deploy")
