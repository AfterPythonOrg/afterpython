[uv]: https://github.com/astral-sh/uv
[poetry]: https://github.com/python-poetry/poetry
[pdm]: https://github.com/pdm-project/pdm
[ruff]: https://github.com/astral-sh/ruff
[ty]: https://github.com/astral-sh/ty
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

`ap init` also adds this to your `pyproject.toml`, so that ruff always finds `afterpython/ruff.toml`:
```toml
[tool.ruff]
extend = "afterpython/ruff.toml"
```
Keep all your ruff settings in `afterpython/ruff.toml`, not in `pyproject.toml` or a `ruff.toml` at the project root.
If `ap init` finds an existing ruff config there, it skips the ruff setup; remove it and run `ap init ruff` to set it up again.

Wrappers (all arguments are passed through to ruff):
- `ap lint` runs `ruff check`, e.g. `ap lint --fix`.
- `ap format` runs `ruff format`, e.g. `ap format --check`.

Or you can just directly use the `ruff` command (and ruff editor extensions) as usual, they use the same config.

The ruff hooks (`ruff-check` and `ruff-format`) and the ruff step of the CI `lint` job only run when `afterpython/ruff.toml` exists.
If you declined ruff during `ap init` (or its setup was skipped), they are removed/skipped; if you use your own ruff config, set up its hooks and CI yourself.

:::{note}
Relative paths in `afterpython/ruff.toml` are resolved from `afterpython/`, not the project root,
e.g. use `"../tests/*"` in `per-file-ignores` to target your project's `tests/` folder.
:::


---
## Type Checking
`afterpython` uses [ty] for type checking, configured in `afterpython/ty.toml`.

- `ap check` runs `ty check` with `afterpython/ty.toml` (all arguments are passed through to ty), e.g. `ap check src/`.

Unlike ruff, ty doesn't support `extend` yet, so `pyproject.toml` can't point to `afterpython/ty.toml`, and ty only finds it when it's told to. So:
- use `ap check` instead of `ty check` (or run `ty check --config-file afterpython/ty.toml` from the project root)
- set up your editor as shown [below](#editor-setup)

Keep all your ty settings in `afterpython/ty.toml`, not in `pyproject.toml` (`[tool.ty]`) or a `ty.toml` at the project root.
If `ap init` finds an existing ty config there, it skips the ty setup; remove it and run `ap init ty` to set it up again.

The `ty` hook (runs `ap check` on every commit) and the CI `typecheck` job only run when `afterpython/ty.toml` exists.
If you declined ty during `ap init` (or its setup was skipped), they are removed/skipped.

:::{note}
Unlike `afterpython/ruff.toml`, relative paths in `afterpython/ty.toml` are resolved from the project root,
e.g. use `"tests/"` to target your project's `tests/` folder.
:::

### Python Environment
ty needs your project's Python environment to resolve imports of installed packages.
It automatically uses the activated virtual environment, or `.venv` at the project root.
For other environments (e.g. `pixi` or `conda`), or if your project has both `.venv` and a `pixi` environment and you want the latter, set it in `afterpython/ty.toml`:
```toml
[environment]
python = ".pixi/envs/default"
```
Packages you only use in some files (e.g. `pytest` in `tests/`) must be installed in that environment too, otherwise ty reports them as unresolved imports.
With `pixi`, that means adding the feature to your default environment, e.g. `default = ["dev", "test"]` in `pixi.toml`.

### Editor Setup
ty's language server (used by editor extensions) doesn't find `afterpython/ty.toml` by itself, you need to set its `configurationFile` setting **in your project's settings**, e.g.

VS Code (`.vscode/settings.json`):
```json
{
  "ty.configurationFile": "./afterpython/ty.toml"
}
```

Zed (`.zed/settings.json`):
```json
{
  "lsp": {
    "ty": {
      "settings": {
        "configurationFile": "./afterpython/ty.toml"
      }
    }
  }
}
```
For other editors, see ty's [editor settings](https://docs.astral.sh/ty/reference/editor-settings/#configurationfile).

:::{warning}
Don't set it in your global (user) settings, ty fails to load projects that don't have `afterpython/ty.toml`.
:::

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
