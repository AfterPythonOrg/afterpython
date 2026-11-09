## [0.4.4](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.3...v0.4.4) - 2026-11-09

### 🐛 Bug Fixes

- Print skipped ruff/ty/git-cliff setup notices at the end of ap init

### ⚙️ Miscellaneous Tasks

- Link .venv to pixi's default environment on activation

## [0.4.3](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.2...v0.4.3) - 2026-11-08

### 🚀 Features

- Warn when a marimo notebook's title heading isn't first

## [0.4.2](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.1...v0.4.2) - 2026-11-08

### 🚀 Features

- Build marimo notebooks in content folders

### 🐛 Bug Fixes

- Issues found dogfooding marimo content on pytrade

### 📚 Documentation

- Document writing content in marimo notebooks

## [0.4.1](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.0...v0.4.1) - 2026-11-07

### 💥 Breaking Changes

- Drop Python 3.12 support

### 🚀 Features

- Dark theme and docstring format option for the pdoc API reference
- Interactive checkbox for ap init setup steps
- Giscus comment section for content pages via [website.comments]
- Default blog myst.yml to article-theme
- Ap init content to initialize individual content types

### 🐛 Bug Fixes

- Indent nested class members in the pdoc API reference sidebar

### 📚 Documentation

- Format ap bump as code in the 0.4.0 changelog
- Comment out DeepWiki badge in README

## [0.4.0] - 2026-10-01

### 💥 Breaking Changes

- Replace commitizen and pre-commit
- Add ty type checking (`ap check`), rename ruff's `ap check` to `ap lint`

### 🚀 Features

- Commit message check can be opted out
- Generate CHANGELOG.md and GitHub release notes with git-cliff

### 🐛 Bug Fixes

- Both ap-commit hooks now put the project's .venv on PATH themselves and call ap directly
- Ruff now uses afterpython/ruff.toml for the whole project, not only files inside afterpython/
- `pcu -u --all` upgrades pixi and prek even when pyproject.toml is up to date
- `ap bump` leaves CHANGELOG.md ending in one newline and unstages it on rollback

### 📚 Documentation

- Remove commitizen
- Replace commitizen docs with the ap-commit hook, [commit.types] and uv-based ap bump

### 🚜 Refactor

- Target py312 in ruff config and use type statements for type aliases

### ⚙️ Miscellaneous Tasks

- Update pixi version to 0.81
- Update github workflows
