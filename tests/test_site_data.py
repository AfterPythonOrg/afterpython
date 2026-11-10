import json
import threading
import time

import pytest

from afterpython.builders import site_data


@pytest.fixture
def site(project):
    (project.website_path / "static").mkdir(parents=True)
    project.build_path.mkdir(parents=True)
    return project


def _source(name: str):
    return next(s for s in site_data._sources({"blog"}) if s.name == name)


def _static_faq(site):
    path = site.website_path / "static" / "faq.json"
    return json.loads(path.read_text()) if path.exists() else None


def test_faq_rebuild_publishes_to_static(site):
    (site.afterpython_path / "faq.yml").write_text("- question: Q1\n  answer: A1\n")
    site_data.rebuild_source(_source("faq.yml"))
    assert _static_faq(site) == [{"question": "Q1", "answer": "A1", "category": ""}]


def test_deleted_faq_removes_stale_json(site):
    faq = site.afterpython_path / "faq.yml"
    faq.write_text("- question: Q1\n  answer: A1\n")
    site_data.rebuild_source(_source("faq.yml"))
    faq.unlink()
    site_data.rebuild_source(_source("faq.yml"))
    assert _static_faq(site) is None
    assert not (site.build_path / "faq.json").exists()


def test_static_files_are_copied(site):
    (site.static_path).mkdir()
    (site.static_path / "logo.svg").write_text("<svg/>")
    site_data.rebuild_source(_source("afterpython/static/"))
    assert (site.website_path / "static" / "logo.svg").read_text() == "<svg/>"


def test_doc_has_no_listing(site):
    assert _source("content listings").outputs == ("blog.json",)
    listings = next(
        s for s in site_data._sources({"doc"}) if s.name == "content listings"
    )
    assert listings.outputs == ()


def test_watcher_rebuilds_on_change_and_survives_errors(site):
    faq = site.afterpython_path / "faq.yml"
    faq.write_text("- question: Q1\n  answer: A1\n")
    stop = threading.Event()
    thread = threading.Thread(
        target=site_data.watch_site_data, args=(set(), stop, 0.05), daemon=True
    )
    thread.start()
    try:

        def wait_for(predicate):
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if predicate():
                    return True
                time.sleep(0.05)
            return False

        # invalid YAML: the watcher reports it and keeps running
        faq.write_text("- question: [unclosed\n")
        time.sleep(0.3)
        assert thread.is_alive()

        faq.write_text("- question: Q2\n  answer: A2\n")
        assert wait_for(lambda: (_static_faq(site) or [{}])[0].get("question") == "Q2")
    finally:
        stop.set()
        thread.join(timeout=2)
