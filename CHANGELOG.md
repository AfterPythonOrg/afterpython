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
