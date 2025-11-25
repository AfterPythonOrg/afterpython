[uv]: https://github.com/astral-sh/uv
[poetry]: https://github.com/python-poetry/poetry
[pdm]: https://github.com/pdm-project/pdm
[ruff]: https://github.com/astral-sh/ruff
[pixi]: https://github.com/prefix-dev/pixi

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

`pcu` (similar to `ncu` in Node.js) helps automate this process:
- `pcu` shows the latest available versions of your dependencies
- `pcu -u` updates the minimum versions in your `pyproject.toml`
- `pcu -u --all` also updates the versions in your `.pre-commit-config.yaml`


You can also run `ap update deps` (`pcu` is an alias for this) to achieve the same effect.


:::{warning}
Only update minimum versions when you have a good reason—such as needing bug fixes, new features, or addressing breaking changes you've adapted to. Otherwise, you're forcing users to upgrade their environments unnecessarily, creating installation barriers without providing any actual benefits.
:::


---
## pixi 🚧
[pixi] manages both your package dependencies and your environment. For example, if your project installs `pyspark` and you need to lock Java to version 17, `pixi` handles that for you.
