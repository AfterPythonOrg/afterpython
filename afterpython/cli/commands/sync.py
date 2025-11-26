from datetime import datetime

import click
from pyproject_metadata import StandardMetadata
from tomlkit.toml_document import TOMLDocument

import afterpython as ap
from afterpython.utils import convert_author_name_to_id


def _sync_authors_yml(authors: list[tuple[str, str | None]]):
    """Sync authors.yml with authors in pyproject.toml"""
    from afterpython._io.yaml import read_yaml
    from afterpython.tools.myst import update_authors_yml

    # read myst.yml from docs path to get "version"
    doc_myst_yml = read_yaml(ap.paths.afterpython_path / "doc" / "myst.yml")
    data = {
        "version": doc_myst_yml["version"],
        "project": {
            "contributors": [
                # NOTE: author is a tuple of (name, email), so author[0] is the name and author[1] is the email
                {
                    "id": convert_author_name_to_id(str(author[0])),
                    "name": str(author[0]),
                    "email": str(author[1]),
                    # "github": ...
                }
                for author in authors
            ]
        },
    }
    update_authors_yml(data)
    click.echo("✓ Synced authors.yml with pyproject.toml")


@click.command()
def sync():
    """Sync between pyproject.toml+afterpython.toml and authors.yml+myst.yml files"""
    from afterpython._io.toml import _from_tomlkit
    from afterpython.const import CONTENT_TYPES
    from afterpython.tools._afterpython import read_afterpython
    from afterpython.tools.myst import update_myst_yml
    from afterpython.tools.pyproject import (
        read_metadata,
        read_pyproject,
        write_pyproject,
    )

    pyproject: StandardMetadata = read_metadata()
    project_name = str(pyproject.name)
    afterpython = read_afterpython()
    github_url = str(pyproject.urls.get("repository", ""))
    company_name = str(_from_tomlkit(afterpython["company"]).get("name", ""))
    company_url = str(_from_tomlkit(afterpython["company"]).get("url", ""))
    website_url = str(_from_tomlkit(afterpython["website"]).get("url", ""))
    authors = pyproject.authors
    if company_name and company_url:
        nav_bar = [{"title": company_name, "url": company_url}]
    else:
        nav_bar = []
    if website_url:
        nav_bar.extend(
            [
                {
                    "title": content_type.capitalize() + "s",
                    "url": f"{website_url}/{content_type}",
                }
                for content_type in CONTENT_TYPES
            ]
        )

    _sync_authors_yml(authors)

    # update "homepage", "repository", and "documentation" in pyproject.toml
    if website_url:
        doc: TOMLDocument = read_pyproject()
        doc["project"]["urls"]["homepage"] = website_url
        doc["project"]["urls"]["documentation"] = f"{website_url}/doc"
        write_pyproject(doc)

    # update myst.yml files for each content type (e.g. doc/, blog/, tutorial/, example/, guide/)
    # based on the current values in pyproject.toml and afterpython.toml
    for content_type in CONTENT_TYPES:
        path = ap.paths.afterpython_path / content_type
        nav_bar_per_content_type = [
            item for item in nav_bar if item["title"] != content_type.capitalize() + "s"
        ]
        title = project_name + f"'s {content_type.capitalize()}"
        data = {
            "project": {
                # using author ids defined in authors.yml
                "authors": [
                    convert_author_name_to_id(str(author[0])) for author in authors
                ],
                "venue": {
                    # NOTE: company's name is used as the venue title
                    "title": company_name,
                    "url": company_url,
                },
                "copyright": f"© {company_name or project_name} {datetime.now().year}. All rights reserved.",
                "title": "",
                "description": str(pyproject.description),
                "keywords": list(map(str, pyproject.keywords)),
                "github": github_url,
            },
            "site": {
                "title": title,
                "options": {
                    "logo_text": project_name,
                    "logo_url": website_url,
                },
                "nav": nav_bar_per_content_type,
                "actions": [
                    {
                        "title": "⭐ Star",
                        "url": github_url,
                    }
                ],
            },
        }
        update_myst_yml(data, path)
        click.echo(
            f"✓ Synced myst.yml in {path.name}/ with pyproject.toml and afterpython.toml"
        )
