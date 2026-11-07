from __future__ import annotations

import json
import re

import click

import afterpython as ap

GISCUS_API = "https://giscus.app/api/discussions/categories"
DEFAULT_CATEGORY = "Announcements"


def _read_comments_config() -> dict:
    from afterpython._io.toml import _from_tomlkit
    from afterpython.tools._afterpython import read_afterpython

    website = _from_tomlkit(read_afterpython().get("website", {}))
    return dict(website.get("comments", {}))


def _get_github_repo() -> str | None:
    """Return "owner/repo" from pyproject.toml's repository URL, or the git remote."""
    from afterpython.tools._git import get_github_url
    from afterpython.tools.pyproject import read_metadata

    url = str(read_metadata().urls.get("repository", "")) or get_github_url() or ""
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    return f"{match[1]}/{match[2]}" if match else None


def _fetch_giscus_categories(repo: str) -> dict:
    """Fetch the repo and category IDs giscus needs. Raises click.ClickException on failure."""
    import httpx2

    try:
        response = httpx2.get(GISCUS_API, params={"repo": repo}, timeout=10.0)
    except httpx2.HTTPError as e:
        raise click.ClickException(f"could not reach giscus.app ({e})") from e
    try:
        data = response.json()
    except ValueError:
        data = {}
    if response.status_code != 200 or "repositoryId" not in data:
        error = data.get("error") or f"HTTP {response.status_code}"
        raise click.ClickException(error)
    return data


def build_comments_json():
    """Build comments.json for the giscus comment section on content pages.

    Reads [website.comments] in afterpython.toml. The website template only
    shows comments when comments.json exists, so a disabled or failed setup
    just leaves it out. Never fails the build.
    """
    stale = ap.paths.website_path / "static" / "comments.json"
    stale.unlink(missing_ok=True)

    config = _read_comments_config()
    if not config.get("enabled", False):
        click.echo("Comments are disabled, skip building comments.json")
        return

    def warn(reason: str):
        click.secho(f"Warning: skip comments, {reason}", fg="yellow")

    repo = _get_github_repo()
    if not repo:
        warn(
            "no GitHub repository found "
            "(set [project.urls] repository in pyproject.toml)"
        )
        return

    category = str(config.get("category") or DEFAULT_CATEGORY)
    try:
        data = _fetch_giscus_categories(repo)
    except click.ClickException as e:
        warn(
            f"giscus is not ready for {repo}: {e.message}\n"
            f"  1. Enable Discussions: https://github.com/{repo}/settings\n"
            "  2. Install the giscus app: https://github.com/apps/giscus\n"
            "  Or set [website.comments] enabled = false in afterpython.toml"
        )
        return

    category_id = next(
        (c["id"] for c in data.get("categories", []) if c["name"] == category), None
    )
    if not category_id:
        names = ", ".join(c["name"] for c in data.get("categories", []))
        warn(
            f'Discussions category "{category}" not found in {repo} '
            f"(available: {names or 'none'})"
        )
        return

    click.echo(f"Building comments.json ({repo}, {category})...")
    comments = {
        "repo": repo,
        "repoId": data["repositoryId"],
        "category": category,
        "categoryId": category_id,
    }
    with open(ap.paths.build_path / "comments.json", "w") as f:
        json.dump(comments, f, indent=2)
