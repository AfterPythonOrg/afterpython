from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Paths:
    user_path: Path = field(init=False)
    afterpython_path: Path = field(init=False)
    website_path: Path = field(init=False)
    build_path: Path = field(init=False)
    static_path: Path = field(init=False)
    docs_path: Path = field(init=False)

    def __post_init__(self):
        self.user_path = self._find_project_root()
        self.afterpython_path = self.user_path / "afterpython"
        self.website_path = self.afterpython_path / "_website"
        self.build_path = self.afterpython_path / "_build"
        self.static_path = self.afterpython_path / "static"
        self.docs_path = self.afterpython_path / "docs"

    def _find_project_root(self) -> Path:
        """Find the project root by looking for pyproject.toml in current or parent directories."""
        current = Path.cwd()

        # Check current directory and all parents
        for path in [current, *current.parents]:
            if (path / "pyproject.toml").exists():
                return path

        # If no pyproject.toml found, raise an error like uv does
        raise FileNotFoundError(
            "No pyproject.toml found in current directory or any parent directory"
        )
