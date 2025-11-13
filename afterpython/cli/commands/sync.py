from datetime import datetime

import click

import afterpython as ap


@click.command()
def sync():
    """Sync between pyproject.toml+afterpython.toml and myst.yml files"""
    from pyproject_metadata import StandardMetadata
    from afterpython.const import CONTENT_TYPES
    from afterpython._io.toml import read_pyproject, read_afterpython, _from_tomlkit
    from afterpython._io.yaml import update_myst_yml
    
    pyproject: StandardMetadata = StandardMetadata.from_pyproject(read_pyproject())
    afterpython = read_afterpython()
    github_url = str(pyproject.urls.get('repository', ''))
    company_name = str(_from_tomlkit(afterpython['company']).get('name', ''))
    company_url = str(_from_tomlkit(afterpython['company']).get('url', ''))
    authors = [str(author[0]).lower().replace(" ", "_") for author in pyproject.authors]
    
    for content_type in CONTENT_TYPES:
        path = getattr(ap.paths, f"{content_type}_path")
        title = str(pyproject.name) + f"'s {content_type.capitalize()}"
        data = {
            'project': {
                # using author ids defined in authors.yml
                "authors": authors,
                "venue": {
                    # NOTE: company's name is used as the venue title
                    "title": company_name,
                    "url": company_url,
                },
                "copyright": f"© {company_name or pyproject.name} {datetime.now().year}. All rights reserved.",
                "title": title,
                "description": str(pyproject.description),
                "keywords": list(pyproject.keywords),
                "github": github_url,
            },
            "site": {
                "title": title,
                "actions": [
                    {
                        "title": "⭐ Star",
                        "url": github_url,
                    }
                ],
            }
        }
        update_myst_yml(data, path)
        click.echo(f"✓ Synced myst.yml in {path.name}/ with pyproject.toml and afterpython.toml")
