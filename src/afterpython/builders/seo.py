"""Post-process the final static site (afterpython/_website/build/) for SEO.

Runs after `pnpm build`, on the HTML that actually gets deployed, so it covers
both the SvelteKit pages and the MyST content pages without touching either
generator:

- one canonical URL per page: `x/index.html` -> `{url}/x/`, `x.html` -> `{url}/x`,
  matching how GitHub Pages serves them (no redirect, no duplicate)
- `<link rel="canonical">` injected into every indexable page
- internal links rewritten to that canonical form, so `/doc/quickstart` (301 on
  GitHub Pages) becomes `/doc/quickstart/`
- `noindex` on the SPA fallback (200.html) and 404.html
- sitemap.xml listing every indexable page, plus a robots.txt pointing to it
"""

from __future__ import annotations

import html
import posixpath
import re
from functools import partial
from pathlib import Path, PurePosixPath
from xml.sax.saxutils import escape

import click

import afterpython as ap

# pages that must not be indexed or listed in the sitemap
NOINDEX_FILES = {"200.html", "404.html"}

_HEAD_OPEN = re.compile(r"<head[^>]*>", re.IGNORECASE)
_CANONICAL = re.compile(r"<link[^>]*rel=[\"']?canonical", re.IGNORECASE)
_ROBOTS_NOINDEX = re.compile(
    r"<meta[^>]*name=[\"']?robots[\"']?[^>]*noindex", re.IGNORECASE
)
# SvelteKit's prerendered redirect, e.g. blog/x.html -> blog/x/ (old post links)
_META_REFRESH = re.compile(r"<meta[^>]*http-equiv=[\"']?refresh", re.IGNORECASE)
# href on any tag, skipping external (scheme:) and fragment-only links
_HREF = re.compile(
    r"""(\shref=)(["'])(?![a-zA-Z][\w+.-]*:|#)([^"']+)\2""", re.IGNORECASE
)


def _canonical_path(rel: PurePosixPath) -> str:
    """URL path (without base path) under which GitHub Pages serves `rel` with a 200."""
    if rel.name == "index.html":
        parent = rel.parent.as_posix()
        return "/" if parent == "." else f"/{parent}/"
    return "/" + rel.with_suffix("").as_posix()


def _is_redirect(text: str) -> bool:
    head = text.split("</head>", 1)[0]
    return bool(_META_REFRESH.search(head))


def _canonical_map(build_dir: Path) -> dict[str, str]:
    """Map every URL path a page answers to (with and without the trailing
    slash) to that page's canonical path."""
    # redirect stubs aren't pages: they never win over x/index.html
    canonicals = {
        _canonical_path(PurePosixPath(f.relative_to(build_dir).as_posix()))
        for f in build_dir.rglob("*.html")
        if not _is_redirect(f.read_text(encoding="utf-8"))
    }
    mapping: dict[str, str] = {}
    for canonical in sorted(canonicals):
        bare = canonical.rstrip("/") or "/"
        # `x.html` wins over `x/index.html` when both exist: it's what
        # SvelteKit prerenders for routes like /faq and /blog
        if canonical != "/" and canonical.endswith("/") and bare in canonicals:
            continue
        mapping[bare] = canonical
        mapping[bare.rstrip("/") + "/"] = canonical
    return mapping


def _rewrite_href(
    match: re.Match,
    page_dir: str,
    base_path: str,
    canonical_by_path: dict[str, str],
) -> str:
    """Fix the trailing slash of an internal link so it doesn't redirect.

    Only the slash changes, so absolute (`/doc/x`) and relative (`./doc`, how
    SvelteKit writes links) hrefs both keep their form.
    """
    prefix, quote, url = match.group(1), match.group(2), match.group(3)
    path, sep, rest = _split_url(url)
    if not path or path.startswith("//"):
        return match.group(0)
    if path.startswith("/"):
        if base_path:
            if path != base_path and not path.startswith(base_path + "/"):
                return match.group(0)
            local = path[len(base_path) :] or "/"
        else:
            local = path
    else:
        local = posixpath.normpath(posixpath.join(page_dir, path))
        if path.endswith("/") and not local.endswith("/"):
            local += "/"
    canonical = canonical_by_path.get(html.unescape(local))
    if canonical is None or canonical == local:
        return match.group(0)
    new_path = path + "/" if canonical.endswith("/") else path.rstrip("/")
    return f"{prefix}{quote}{new_path}{sep}{rest}{quote}"


def _split_url(url: str) -> tuple[str, str, str]:
    """Split '/a/b?x#y' into ('/a/b', '?', 'x#y')."""
    for i, ch in enumerate(url):
        if ch in "?#":
            return url[:i], ch, url[i + 1 :]
    return url, "", ""


def _read_website_url() -> str:
    from afterpython._io.toml import _from_tomlkit
    from afterpython.tools._afterpython import read_afterpython

    website = _from_tomlkit(read_afterpython().get("website", {}))
    return str(website.get("url", "")).strip().rstrip("/")


def build_seo(base_path: str = ""):
    """Add canonical tags, fix internal links and write sitemap.xml/robots.txt.

    Args:
        base_path: BASE_PATH the site was built with ("" for a custom domain,
            "/repo" for a default GitHub Pages URL); internal links carry it.
    """
    build_dir = ap.paths.website_path / "build"
    if not build_dir.exists():
        return
    website_url = _read_website_url()
    if not website_url:
        click.echo(
            "Warning: [website].url is not set in afterpython.toml, "
            "skipping canonical tags and sitemap.xml"
        )
        return
    # website.url already includes the base path for github.io sites
    site_root = website_url
    if base_path and website_url.endswith(base_path):
        site_root = website_url[: -len(base_path)]

    click.echo("Adding canonical tags and building sitemap.xml...")
    canonical_by_path = _canonical_map(build_dir)

    sitemap_urls: list[str] = []
    for file in sorted(build_dir.rglob("*.html")):
        rel = PurePosixPath(file.relative_to(build_dir).as_posix())
        text = file.read_text(encoding="utf-8")
        original = text
        if _is_redirect(text):
            continue
        noindex = rel.as_posix() in NOINDEX_FILES or bool(_ROBOTS_NOINDEX.search(text))

        page_path = _canonical_path(rel)
        # directory relative links resolve against: /x/ for x/index.html, / for x.html
        page_dir = (
            page_path if page_path.endswith("/") else posixpath.dirname(page_path)
        )
        text = _HREF.sub(
            partial(
                _rewrite_href,
                page_dir=page_dir,
                base_path=base_path,
                canonical_by_path=canonical_by_path,
            ),
            text,
        )
        # a shadowed x/index.html points at its x.html twin
        canonical_url = (
            site_root + base_path + canonical_by_path.get(page_path, page_path)
        )

        head = _HEAD_OPEN.search(text)
        if head:
            if rel.as_posix() in NOINDEX_FILES and not _ROBOTS_NOINDEX.search(text):
                tag = '<meta name="robots" content="noindex">'
                text = text[: head.end()] + tag + text[head.end() :]
            elif not noindex and not _CANONICAL.search(text):
                tag = f'<link rel="canonical" href="{html.escape(canonical_url)}">'
                text = text[: head.end()] + tag + text[head.end() :]

        if not noindex and head:
            sitemap_urls.append(canonical_url)
        if text != original:
            file.write_text(text, encoding="utf-8")

    _write_sitemap(build_dir, sitemap_urls)
    _write_robots_txt(build_dir, f"{site_root}{base_path}/sitemap.xml")
    click.echo(f"✓ sitemap.xml lists {len(sitemap_urls)} pages")


def _write_sitemap(build_dir: Path, urls: list[str]):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    lines.extend(f"  <url><loc>{escape(url)}</loc></url>" for url in sorted(set(urls)))
    lines.append("</urlset>")
    (build_dir / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_robots_txt(build_dir: Path, sitemap_url: str):
    """Write robots.txt, or add the Sitemap line to a user-provided one."""
    robots = build_dir / "robots.txt"
    line = f"Sitemap: {sitemap_url}"
    if robots.exists():
        text = robots.read_text(encoding="utf-8")
        if "sitemap:" in text.lower():
            return
        robots.write_text(text.rstrip("\n") + f"\n\n{line}\n", encoding="utf-8")
    else:
        robots.write_text(f"User-agent: *\nAllow: /\n\n{line}\n", encoding="utf-8")
