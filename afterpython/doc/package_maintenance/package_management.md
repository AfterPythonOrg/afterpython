[uv]: https://github.com/astral-sh/uv
[poetry]: https://github.com/python-poetry/poetry
[pdm]: https://github.com/pdm-project/pdm
[ruff]: https://github.com/astral-sh/ruff
[pixi]: https://github.com/prefix-dev/pixi
[npm-check-updates]: https://www.npmjs.com/package/npm-check-updates

# Package Management

## Dependency Management
`afterpython` doesn’t manage your dependencies or lock you into a tool. Choose what you prefer:
- [uv] (what `afterpython`’s wrapper commands call)
- [pdm]
- [poetry]

Example wrapper:
- `ap install` runs `uv sync --all-extras --all-groups`.


---
## Linting and Formatting
`afterpython` uses [ruff] for linting and formatting, configured in `afterpython/ruff.toml`.

Example wrapper:
- `ap check` (alias: `ap lint`) runs `ruff check --config ./afterpython/ruff.toml`.

Or you can just directly use `ruff` command as usual since it will automatically find the config file in `afterpython/ruff.toml`.


---
## Python Check Updates (`pcu`)
As a package maintainer, you face a dilemma: your dependencies (e.g. `pandas`) release new versions with bug fixes and features, but updating the minimum versions (e.g. `pandas>=2.0.0`) in your `pyproject.toml` means dropping support for users with older versions.

This is why minimum version updates are usually done manually—it's up to the package maintainer to decide when to require newer dependency versions.

`pcu` (similar to `ncu` ([npm-check-updates]) in Node.js) helps automate this process:
- `pcu` shows the latest available versions of your dependencies
- `pcu -u` updates the minimum versions in your `pyproject.toml`
- `pcu -u --all` also updates the versions in your `.pre-commit-config.yaml`


You can also run `ap update deps` (`pcu` is an alias for this) to achieve the same effect.


:::{warning}
Only update minimum versions when you have a good reason—such as needing bug fixes, new features, or addressing breaking changes you've adapted to. Otherwise, you're forcing users to upgrade their environments unnecessarily, creating installation barriers without providing any actual benefits.
:::


---
## `pixi`
[pixi] is a system-level package and environment manager that handles both Python and non-Python dependencies. For example, if your project uses `pyspark` and you need to lock Java to version 17, `pixi` can handle that for you.

`afterpython` itself uses `pixi` to create a reproducible development environment.
For instance, `afterpython` uses `gh` (the GitHub CLI), which is a non-Python dependency. Using `pixi` ensures all contributors use the exact same version of `gh` and other system tools. If you're already using `pixi` for your project, `afterpython` provides a set of commands that keep both `uv` and `pixi` synchronized:
- `ap add <lib>` — Adds a package to both `uv` and `pixi`. Supports `--optional` and `--group` flags.
- `ap remove <lib>` — Removes a package from both `uv` and `pixi`. Supports `--optional` and `--group` flags.
- `ap lock` — Runs both `uv lock` and `pixi lock`
- `ap install` — Runs `uv sync --all-extras --all-groups` and `pixi install`
