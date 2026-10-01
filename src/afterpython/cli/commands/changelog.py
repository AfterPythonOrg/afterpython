import subprocess

import click
from click.exceptions import Exit

import afterpython as ap


@click.command(
    add_help_option=False,  # disable click's --help option so that git-cliff --help can work
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def changelog(ctx):
    """Preview the changelog with git-cliff (using afterpython/cliff.toml)

    \b
    Without arguments, prints the unreleased changes, i.e. the section
    the next stable `ap bump` will add to CHANGELOG.md.
    Any arguments are passed to git-cliff instead, e.g.
    `ap changelog --latest` for the latest release.
    """
    from afterpython.cli.commands.bump import PRE_RELEASE_TAGS
    from afterpython.utils import handle_passthrough_help

    # Show both our options and git-cliff's help and exit
    handle_passthrough_help(ctx, ["git-cliff"], show_underlying=True)

    cliff_toml_path = ap.paths.afterpython_path / "cliff.toml"
    if not cliff_toml_path.exists():
        raise click.ClickException(
            f"{cliff_toml_path} not found, run `ap init cliff` first"
        )
    cmd = ["git-cliff", "--config", str(cliff_toml_path)]
    # like `ap bump`: no sections for pre-release and dev tags,
    # their commits belong to the next stable release
    if "--ignore-tags" not in ctx.args:
        cmd += ["--ignore-tags", PRE_RELEASE_TAGS]
    args = ctx.args or ["--unreleased"]
    result = subprocess.run([*cmd, *args], cwd=ap.paths.user_path, check=False)
    if result.returncode != 0:
        raise Exit(result.returncode)
