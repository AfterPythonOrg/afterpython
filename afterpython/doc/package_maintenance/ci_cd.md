[PyPI]: https://pypi.org/

# CI/CD Pipelines
Currently, `afterpython` only supports GitHub Actions for CI/CD pipelines.

## GitHub Actions
Inside `.github/workflows/`, you'll find the following workflows:

### `ci.yml`
Runs linting and formatting with ruff, runs tests with pytest and builds the package and verifies it can be installed with `uv build`.

### `release.yml` (optional)
Releases your package to [PyPI] and GitHub.

`release.yml` will NOT be created if `commitizen` is not initialized during `ap init`.

See [PyPI and GitHub Releases](./release_management.md#pypi-and-github-releases) for more details.

### `deploy.yml`
Deploys your project website to GitHub Pages.

### `dependabot.yml` (optional)
Automatically updates GitHub Actions versions.

---
## Security Scanning 🚧

---
## Code Coverage 🚧
