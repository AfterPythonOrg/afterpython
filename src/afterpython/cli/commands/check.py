# NOTE: ty has no `extend` option yet (unlike ruff), so we must pass --config-file ourselves,
# and plain `ty` / editors don't find afterpython/ty.toml without extra setup.
# TODO: once ty supports `extend`, migrate to pyproject.toml's
# [tool.ty] extend = "afterpython/ty.toml" (like [tool.ruff]) and drop --config-file here.
# NOTE: the ty hook runs this command (see pre-commit-config-template.yaml for why it's not
# the official astral-sh/ty-pre-commit hook), so it uses the same config and environment.
import subprocess

import click
from click.exceptions import Exit

import afterpython as ap


@click.command(
    add_help_option=False,  # disable click's --help option so that ty check --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def check(ctx):
    """Run ty type checker"""
    from afterpython.utils import handle_passthrough_help

    # Show both our options and ty's help and exit
    handle_passthrough_help(
        ctx,
        ["ty", "check"],
        show_underlying=True,
    )

    # absolute paths so that it works from any folder, e.g. inside afterpython/
    # (ty would otherwise treat the folder with the nearest ty.toml as the project root)
    cmd = ["ty", "check", "--project", str(ap.paths.user_path)]
    ty_toml_path = ap.paths.afterpython_path / "ty.toml"
    # without afterpython/ty.toml, let ty find its config itself (e.g. the user's own [tool.ty])
    if ty_toml_path.exists():
        cmd += ["--config-file", str(ty_toml_path)]
    result = subprocess.run([*cmd, *ctx.args], check=False)
    if result.returncode != 0:
        raise Exit(result.returncode)
