[prek]: https://prek.j178.dev/
[Conventional Commits]: https://www.conventionalcommits.org


# Commit Workflow

## Pre-Commit Hooks
Pre-commit hooks are scripts that automatically run before a commit is finalized, serving as a quality checkpoint for code changes. `afterpython` uses [prek] (a faster drop-in replacement for `pre-commit`) to manage these hooks.

After running `ap init`, if you agreed to create a `.pre-commit-config.yaml` file, it will be located in the `afterpython/` folder with some default hooks. Since this configuration file is not at the project root, you need to run `ap prek` (or `ap pc` for short) instead of the `prek` command—it automatically uses the configuration in `afterpython/`.

### Commands
- `ap prek` (or `ap pc`) — equivalent to `prek --config afterpython/.pre-commit-config.yaml`


---
## Commit Messages
`afterpython` checks that your commit messages follow the [Conventional Commits] format, e.g. `feat: add new feature`, `fix(cli): resolve bug`. This is done by the `ap-commit` hook in `afterpython/.pre-commit-config.yaml`, so just use `git commit` as usual.

### Writing Commit Messages
- `git commit` — when your editor opens, the format and the allowed commit types are listed above git's own comments.
- `git commit -m "feat: add new feature"` — the message is checked the same way.

The message title must look like `<type>(<scope>): <description>`, where `(<scope>)` is optional and `<type>` is one of the allowed commit types. Add `!` before `:` for breaking changes, e.g. `feat!: drop Python 3.11`.
Messages created by git itself (e.g. merge, revert, `fixup!` and `squash!` commits) are let through as-is.

If the message is rejected, it is saved, so you can edit and retry with the `git commit -e -F <file>` command shown in the error.

### Commit Types
Commit types can be defined in `afterpython/afterpython.toml` (`type = "description"`), `ap init` creates it with these defaults:
```toml
# allowed commit types, e.g. "feat: add X"; add or remove lines freely
[commit.types]
feat = "A new feature"
fix = "A bug fix"
docs = "Documentation only changes"
style = "Formatting, no code meaning change"
refactor = "Neither fixes a bug nor adds a feature"
perf = "Performance improvement"
test = "Adding or fixing tests"
build = "Build system or dependencies"
ci = "CI configuration"
chore = "Other changes that don't modify src or tests"
wip = "Work in progress"
```
To allow a new type, add a line, e.g. `deps = "Dependency updates"`; to disallow one, remove its line. The descriptions are shown in the commit message template and in the error message when a commit is rejected.

:::{note} Opting out
Commit messages are only checked when `[commit.types]` has at least one type.
To opt out, remove the section or leave it empty. If you opted out during `ap init`, the section is commented out, uncomment it to opt in.
:::

### Bypassing Checks
- `SKIP=ap-commit git commit` — skip the commit message check
- `git commit --no-verify` — skip all pre-commit and commit message hooks
- `git push --no-verify` — skip all pre-push hooks
