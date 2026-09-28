[uv]: https://docs.astral.sh/uv/
[SemVer]: https://semver.org
[Python Versioning]: https://packaging.python.org/en/latest/discussions/versioning/
[PyPI]: https://pypi.org/


# Package Releases

## Version Bumping
`ap bump` increments your project version using [uv]'s `uv version --bump` under the hood, then commits the change (`bump: version A → B`) and tags it (e.g. `v0.1.0`).

### Commands
- `ap bump` — bump version within the current release phase
    - dev versions: `0.1.0.dev3` → `0.1.0.dev4`
    - pre-releases: `0.1.0a1` → `0.1.0a2`
    - stable versions: `0.3.19` → `0.3.20` (patch)
- `ap bump --minor` / `ap bump --major` — bump the minor / major version instead of patch (stable versions only, e.g., `0.3.19` → `0.4.0` / `1.0.0`)
- `ap bump --pre` — bump to a pre-release version (e.g., `0.1.0.dev3` → `0.1.0rc0`)
- `ap bump --release` — bump to a release version (e.g., `0.1.0rc0` → `0.1.0`), only allowed on the default branch (e.g. `main`)
    - **NOTE**: This command will **automatically trigger** the [release](./package_releases.md#releasing-your-package) workflow, you don't need to run `ap release` manually.

:::{seealso} Versioning
:class: dropdown
See [SemVer] and [Python Versioning] to learn more about versioning in Python packages.
:::

---
## PyPI and GitHub Releases
If you agreed to create the release workflow during `ap init`, `afterpython` creates a GitHub Actions workflow (`.github/workflows/release.yml`) that publishes your package to [PyPI] and creates GitHub releases.

### PyPI Setup
To enable trusted publishing on PyPI:

1. Go to [PyPI] and navigate to your project
2. Click **Manage** → **Publishing** (left sidebar)
3. Under the **GitHub** tab, fill in:
   - **Owner:** Your GitHub username or organization name
   - **Repository:** Your repository name
   - **Workflow name:** `release.yml`

:::{note} Using an API Token
:class: dropdown
To use an API token instead (e.g., `UV_PUBLISH_TOKEN`), you'll need to modify the `release.yml` workflow file.
:::

### Releasing Your Package
`ap release` manually pushes the git tag created by `ap bump` to GitHub, which triggers the `release.yml` workflow. This command is unnecessary if you've already successfully run `ap bump --release`.

**Commands:**
- `ap release` — release the current version to PyPI and GitHub
- `ap release --force` — force release even for development versions


---
## Semantic Release 🚧


---
## Changlog 🚧
