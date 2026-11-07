import json

import pytest

from afterpython.builders import build_comments_json

CATEGORIES = {
    "repositoryId": "R_repo",
    "categories": [
        {"id": "DIC_ann", "name": "Announcements"},
        {"id": "DIC_dev", "name": "Dev Comments"},
    ],
}


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


@pytest.fixture
def setup(project, monkeypatch):
    """Write afterpython.toml, mock the giscus API, and return the comments.json path."""
    project.build_path.mkdir(parents=True, exist_ok=True)
    (project.user_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n'
        '[project.urls]\nrepository = "https://github.com/owner/demo"\n'
    )
    response = {"value": FakeResponse(200, CATEGORIES)}
    monkeypatch.setattr("httpx2.get", lambda *args, **kwargs: response["value"])

    def _setup(comments: str, api_response: FakeResponse | None = None):
        (project.afterpython_path / "afterpython.toml").write_text(
            f"[website.comments]\n{comments}\n"
        )
        if api_response:
            response["value"] = api_response
        return project.build_path / "comments.json"

    return _setup


def test_enabled_writes_comments_json(setup):
    out = setup("enabled = true")
    build_comments_json()
    assert json.loads(out.read_text()) == {
        "repo": "owner/demo",
        "repoId": "R_repo",
        "category": "Announcements",
        "categoryId": "DIC_ann",
    }


def test_custom_category(setup):
    out = setup('enabled = true\ncategory = "Dev Comments"')
    build_comments_json()
    assert json.loads(out.read_text())["categoryId"] == "DIC_dev"


def test_disabled_skips_and_removes_stale(setup, project):
    stale = project.website_path / "static" / "comments.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    out = setup("enabled = false")
    build_comments_json()
    assert not out.exists()
    assert not stale.exists()


def test_giscus_not_installed_skips(setup, capsys):
    out = setup(
        "enabled = true",
        FakeResponse(403, {"error": "giscus is not installed on this repository"}),
    )
    build_comments_json()
    assert not out.exists()
    assert "giscus is not installed" in capsys.readouterr().out


def test_unknown_category_skips(setup, capsys):
    out = setup('enabled = true\ncategory = "Nope"')
    build_comments_json()
    assert not out.exists()
    assert 'category "Nope" not found' in capsys.readouterr().out
