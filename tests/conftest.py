import pytest

import afterpython as ap
from afterpython._paths import Paths


@pytest.fixture
def project(tmp_path, monkeypatch):
    """An empty project (pyproject.toml + afterpython/) that `ap.paths` points to."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n')
    (tmp_path / "afterpython").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ap, "paths", Paths())
    return ap.paths
