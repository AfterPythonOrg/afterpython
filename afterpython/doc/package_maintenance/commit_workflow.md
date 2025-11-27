[pre-commit]: https://pre-commit.com/
[commitizen]: https://commitizen-tools.github.io/commitizen/
[Conventional Commits]: https://www.conventionalcommits.org


# Commit Workflow

## Pre-Commit Hooks
Pre-commit hooks are scripts that automatically run before a commit is finalized, serving as a quality checkpoint for code changes. `afterpython` uses [pre-commit] to manage these hooks.

After running `ap init`, if you agreed to create a `.pre-commit-config.yaml` file, it will be located in the `afterpython/` folder with some default hooks. Since this configuration file is not at the project root, you need to run `ap pre-commit` (or `ap pc` for short) instead of the  `pre-commit` command—it automatically uses the configuration in `afterpython/`.

### Commands
- `ap pre-commit` (or `ap pc`) — equivalent to `pre-commit --config afterpython/.pre-commit-config.yaml`


---
## Commitizen
If you agreed to create a `cz.toml` file during `ap init`, `afterpython` will use [commitizen] to help you write clear, structured commit messages following the [Conventional Commits] specification.

Since the `cz.toml` configuration file is located in `afterpython/` (not the project root), use `ap cz` instead of the standard `cz` command.

### Writing Commit Messages
**Recommended:** Use `ap commit` to create commits. This command:
1. Runs pre-commit hooks on changed files to catch issues early
2. Guides you through an interactive prompt to write a properly formatted commit message
3. Provides flags to skip checks when needed

**Alternative:** Use `git commit` directly if you're comfortable writing [Conventional Commits] format messages (e.g., `feat: add new feature`, `fix: resolve bug`). Your message must match the format enforced in `cz.toml` and pass pre-commit hook checks.


**Bypassing checks:** To commit without running any checks:
- `git commit --no-verify` — skip pre-commit hooks
- `git push --no-verify` — skip pre-push hooks

### Commands
- `ap cz` (or `ap commitizen`) — equivalent to `cz --config afterpython/cz.toml`
- `ap commit` — wrapper around `cz commit` with additional features:
    - `ap commit --no-cz` — skip commitizen checks in pre-commit hooks
    - `ap commit --no-pc` — skip pre-commit checks before writing the commit message
- `git commit --no-verify` — skip all pre-commit hooks
- `git push --no-verify` — skip all pre-push hooks


:::{tip} Commitizen Customization
<!-- :class: dropdown -->
Customize the commit message format by editing `cz.toml`.

See [Commitizen Customization](https://commitizen-tools.github.io/commitizen/customization/) for details.
:::
