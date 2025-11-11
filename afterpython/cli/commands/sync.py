from datetime import datetime

import click


@click.group(invoke_without_command=True)
@click.option('--all', is_flag=True, help='Sync both afterpython.toml and myst.yml')
@click.pass_context
def sync(ctx, all: bool):
    """Sync configuration between pyproject.toml, afterpython.toml and myst.yml etc."""
    # If no subcommand provided, default to 'afterpython'
    if ctx.invoked_subcommand is None:
        if all:
            ctx.invoke(afterpython)
            ctx.invoke(myst)
        else:
            ctx.invoke(afterpython)


@sync.command()
def afterpython():
    """Sync afterpython.toml [docs] with pyproject.toml"""
    from pyproject_metadata import StandardMetadata, License
    from afterpython.utils.toml import read_pyproject, update_afterpython_toml
    from afterpython.utils.utils import detect_license_from_file
    
    metadata: StandardMetadata = StandardMetadata.from_pyproject(read_pyproject())
    if isinstance(metadata.license, str):
        metadata.license = License(text=metadata.license, file=None)
    data = {
        'docs': {
            "title": metadata.name + "'s Documentation",
            "description": metadata.description,
            "keywords": metadata.keywords,
            "authors": [{'name': author[0], 'email': author[-1]} for author in metadata.authors],
            "github": metadata.urls['repository'],
            "license": metadata.license.text if metadata.license.file is None else detect_license_from_file(metadata.license.file),
            "copyright": f"© {metadata.name} {datetime.now().year}. All rights reserved."
        }
    }
    update_afterpython_toml(data)
    click.echo("✓ Synced afterpython.toml [docs] with pyproject.toml")
    
    
@sync.command()
def myst():
    """Sync myst.yml [project] section with afterpython.toml [docs] section"""
    from afterpython.utils.toml import read_afterpython_toml, _from_tomlkit
    from afterpython.utils.yaml import read_myst_yml, update_myst_yml

    afterpython_toml = read_afterpython_toml()
    # convert tomlkit objects to plain Python data structures
    docs = _from_tomlkit(afterpython_toml['docs'])
    myst_yml = read_myst_yml()
    data = {
        'project': {
            'id': myst_yml['project']['id'],
            'title': docs['title'],
            'description': docs['description'],
            'keywords': docs['keywords'],
            'authors': docs['authors'],
            'github': docs['github'],
            'license': docs['license'],
            'copyright': docs['copyright'],
        }
    }
    update_myst_yml(data)
    click.echo("✓ Synced myst.yml with afterpython.toml [docs] section")
