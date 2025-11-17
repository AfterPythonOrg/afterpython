from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from afterpython._typing import NodeEnv

import subprocess

import click


command_kwargs = {
    'add_help_option': False,  # disable click's --help option so that myst start --help can work
    'context_settings': dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
}


@click.command(**command_kwargs)
@click.pass_context
@click.option('--doc', is_flag=True, help='Start the development server for doc/ directory')
@click.option('--blog', is_flag=True, help='Start the development server for blog/ directory')
@click.option('--tutorial', is_flag=True, help='Start the development server for tutorial/ directory')
@click.option('--example', is_flag=True, help='Start the development server for example/ directory')
@click.option('--guide', is_flag=True, help='Start the development server for guide/ directory')
def start(ctx, doc: bool, blog: bool, tutorial: bool, example: bool, guide: bool):
    """Simple wrapper for `myst start` for convenience"""
    from afterpython.utils import find_node_env
    from afterpython.const import CONTENT_TYPES
    
    node_env: NodeEnv = find_node_env()
    paths = ctx.obj["paths"]

    if doc:
        content_type = "doc"
    elif blog:
        content_type = "blog"
    elif tutorial:
        content_type = "tutorial"
    elif example:
        content_type = "example"
    elif guide:
        content_type = "guide"
    else:
        raise click.ClickException("No content type specified")
    
    assert content_type in CONTENT_TYPES, f"Invalid content type: {content_type}"

    
    # assert only one of the options is True
    if sum([doc, blog, tutorial, example, guide]) != 1:
        raise click.ClickException("Only one content type can be specified")
    
    content_path = paths.afterpython_path / content_type

    # Check if directory has any content files
    has_content = any(
        content_path.glob('*.md') or
        content_path.glob('*.ipynb') or
        content_path.glob('*.tex')
    )

    if not has_content:
        click.echo(f"Skipping {content_type}/ (no content files found)")
        return

    subprocess.run(["myst", "start", *ctx.args], cwd=content_path, env=node_env, check=True)


def _run(ctx):
    # Get the name of the function that called _run
    import inspect
    caller_frame = inspect.currentframe().f_back
    command_name = caller_frame.f_code.co_name  # e.g. doc, blog, tutorial, example, guide
    
    # Create a new context for start that includes extra args for `myst start`
    with start.make_context('start', [f"--{command_name}", *ctx.args], parent=ctx.parent) as start_ctx:
        return start.invoke(start_ctx)
    

@click.command(**command_kwargs)
@click.pass_context
def doc(ctx):
    """Start the development server for doc/ directory (equivalent to: start --doc)"""
    _run(ctx)


@click.command(**command_kwargs)
@click.pass_context
def blog(ctx):
    """Start the development server for blog/ directory (equivalent to: start --blog)"""
    _run(ctx)


@click.command(**command_kwargs)
@click.pass_context
def tutorial(ctx):
    """Start the development server for tutorial/ directory (equivalent to: start --tutorial)"""
    _run(ctx)

    
@click.command(**command_kwargs)
@click.pass_context
def example(ctx):
    """Start the development server for example/ directory (equivalent to: start --example)"""
    _run(ctx)


@click.command(**command_kwargs)
@click.pass_context
def guide(ctx):
    """Start the development server for guide/ directory (equivalent to: start --guide)"""
    _run(ctx)
