"""`ap dev`: rebuild the website's data files when their sources change.

`prebuild()` and `postbuild()` turn project files into data files under
afterpython/_build/ (faq.json, metadata.json, blog.json, ...) and copy them to
afterpython/_website/static/, where SvelteKit reads them. Without this
watcher that only happens once, when `ap dev` starts, so editing e.g. faq.yml
needed a restart to show up.

Each `_Source` below pairs the files to watch with the builder that reads
them and the outputs that builder writes. The MyST pages themselves are
already live (`myst start` watches them); what goes stale is the data built
around them, such as the blog/tutorial listings.
"""

from __future__ import annotations

import shutil
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import click

import afterpython as ap
from afterpython.const import CONTENT_TYPES


@dataclass(frozen=True)
class _Source:
    name: str
    # returns the files to watch; re-evaluated on every poll so newly
    # created files (e.g. a first faq.yml, a new blog post) are picked up
    files: Callable[[], Iterable[Path]]
    build: Callable[[], None]
    # paths relative to afterpython/_build/ that `build` writes; they are
    # removed before rebuilding so a deleted source doesn't leave stale data
    outputs: tuple[str, ...] = ()


def _rglob_files(path: Path, pattern: str = "*") -> list[Path]:
    if not path.exists():
        return []
    return [p for p in path.rglob(pattern) if p.is_file()]


def _build_faq():
    from afterpython.builders.faq_json import build_faq_json

    build_faq_json()


def _build_metadata():
    from afterpython.builders.metadata import build_metadata

    build_metadata()


def _build_comments():
    from afterpython.builders.comments_json import build_comments_json

    build_comments_json()


def _build_readme_py():
    from afterpython.builders.marimo_notebook import build_marimo_readme

    build_marimo_readme()


def _build_content_listings():
    from afterpython.builders.content_json import build_content_json

    build_content_json()
    # thumbnails and other images referenced by the listings, mirroring the
    # dev branch of postbuild()
    for content_type in CONTENT_TYPES:
        public = ap.paths.afterpython_path / content_type / "_build" / "site" / "public"
        if public.exists():
            shutil.copytree(
                public,
                ap.paths.website_path / "static" / content_type / "build",
                dirs_exist_ok=True,
            )


def _copy_static():
    # afterpython/static/ is copied as-is in postbuild(); there is nothing to
    # build. Deleted files are left in _website/static/ because the template
    # ships its own files there too and we can't tell them apart.
    if ap.paths.static_path.exists():
        shutil.copytree(
            ap.paths.static_path, ap.paths.website_path / "static", dirs_exist_ok=True
        )


def _sources(content_types: set[str]) -> list[_Source]:
    afterpython_path = ap.paths.afterpython_path
    config_files = [ap.paths.pyproject_path, afterpython_path / "afterpython.toml"]
    readme_py = afterpython_path / "README.py"
    # content types with a listing page; doc has none
    listed = sorted(ct for ct in content_types if ct != "doc")
    return [
        _Source(
            name="faq.yml",
            files=lambda: [afterpython_path / "faq.yml"],
            build=_build_faq,
            outputs=("faq.json",),
        ),
        _Source(
            name="project metadata",
            # README.md feeds the home page description
            files=lambda: [
                *config_files,
                readme_py,
                *ap.paths.user_path.glob("README*"),
            ],
            build=_build_metadata,
            outputs=("metadata.json",),
        ),
        _Source(
            # separate from metadata: it calls the giscus API, which README
            # edits shouldn't trigger
            name="comments config",
            files=lambda: config_files,
            build=_build_comments,
            outputs=("comments.json",),
        ),
        _Source(
            name="README.py",
            files=lambda: [readme_py],
            build=_build_readme_py,
            outputs=("readme_py",),
        ),
        _Source(
            name="afterpython/static/",
            files=lambda: _rglob_files(ap.paths.static_path),
            build=_copy_static,
        ),
        _Source(
            name="content listings",
            # `myst start` rewrites these JSON files whenever a page changes
            files=lambda: [
                path
                for ct in listed
                for path in _rglob_files(
                    afterpython_path / ct / "_build" / "site", "*.json"
                )
            ],
            build=_build_content_listings,
            outputs=tuple(f"{ct}.json" for ct in listed),
        ),
    ]


def _snapshot(source: _Source) -> dict[Path, float]:
    mtimes = {}
    for path in source.files():
        try:
            mtimes[path] = path.stat().st_mtime
        except OSError:  # missing, or deleted mid-scan
            continue
    return mtimes


def _remove(path: Path):
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def rebuild_source(source: _Source):
    """Rebuild one source and publish its outputs to _website/static/."""
    build_path = ap.paths.build_path
    website_static = ap.paths.website_path / "static"
    for output in source.outputs:
        _remove(build_path / output)
        _remove(website_static / output)
    source.build()
    for output in source.outputs:
        built = build_path / output
        if built.is_dir():
            shutil.copytree(built, website_static / output, dirs_exist_ok=True)
        elif built.exists():
            shutil.copy2(built, website_static / output)


def watch_site_data(
    content_types: set[str], stop_event: threading.Event, interval: float = 1.0
):
    """Rebuild a source's data files whenever one of its files changes.

    Best effort: a half-saved or invalid file prints an error and the watcher
    keeps going, so the next save can fix it.
    """
    sources = _sources(content_types)
    seen = {source.name: _snapshot(source) for source in sources}
    while not stop_event.wait(interval):
        for source in sources:
            current = _snapshot(source)
            if current == seen[source.name]:
                continue
            seen[source.name] = current
            click.echo(
                click.style(f"↻ {source.name} changed, rebuilding...", fg="cyan")
            )
            try:
                rebuild_source(source)
            except click.ClickException as e:
                click.echo(click.style(f"✗ {e.format_message()}", fg="red"))
            except Exception as e:  # keep watching: a crash here would go unnoticed
                click.echo(
                    click.style(f"✗ rebuilding {source.name} failed: {e!r}", fg="red")
                )
