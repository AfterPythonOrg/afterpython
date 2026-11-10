## [0.5.0](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.9...v0.5.0) - 2026-11-10

### 🚀 Features

- Generate sitemap.xml and canonical tags for the built website
- Use the configurable homepage title and redirect-free website links

### 🐛 Bug Fixes

- Point the pdoc failure hint at api_reference = false

### ⚙️ Miscellaneous Tasks

- Use the authors key in authors.yml

## [0.4.9](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.8...v0.4.9) - 2026-11-10

### 🐛 Bug Fixes

- Keep the clicked FAQ question highlighted in the sidebar
- Default the blog site to book-theme

## [0.4.8](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.7...v0.4.8) - 2026-11-10

### 🚀 Features

- Rebuild website data files on change during ap dev
- Add ap dev --no-readme-py to skip the marimo README.py export

### ⚙️ Miscellaneous Tasks

- Sync the website with project-website-template 0.4.2 (FAQ redesign)

## [0.4.7](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.6...v0.4.7) - 2026-11-10

### 🐛 Bug Fixes

- Shrink the pdoc logo and support a dark logo in the API reference

## [0.4.6](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.5...v0.4.6) - 2026-11-09

### 🐛 Bug Fixes

- Gitignore marimo's __marimo__/ session cache at the project root

## [0.4.5](https://github.com/AfterPythonOrg/afterpython/compare/v0.4.4...v0.4.5) - 2026-11-09

### 🐛 Bug Fixes

- Only run the ty hook when python files are staged

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
