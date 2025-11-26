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
## Branch Protection Rules
To create default branch protection rules:
1. install GitHub CLI
    - on macOS: `brew install gh`
    - on Linux: https://github.com/cli/cli/releases
    - on Windows: https://cli.github.com/
2. authenticate with GitHub CLI by running `gh auth login`
3. run `ap init-branch-rules`, this will create **3 branch protection rules** (a ruleset named `afterpython-default`) for your `main` branch.
    - No Force Pushes
        - Prevents overwriting history on the main branch.
	- No Branch Deletion
        - Protects the main branch from being deleted.
	- CI Status Checks (before the branch can be updated)
        - Requires all configured CI checks to pass before any update (push or PR merge) is allowed.

You can view them in **GitHub → Settings → Rules → Rulesets**


---
## Security Scanning 🚧

---
## Code Coverage 🚧
