import shutil
import subprocess

import afterpython as ap
from afterpython._io.yaml import read_yaml, write_yaml

# tool -> (its config file in afterpython/, a hook id that identifies its repo block)
# a tool's hooks are only kept when its config file exists, see sync_hooks()
# (hook ids, not repo urls, since e.g. the ty hook is in its own `repo: local` block)
TOOL_HOOKS = {
    "ruff": ("ruff.toml", "ruff-check"),
    "ty": ("ty.toml", "ty"),
}


def install_prek():
    # installed in .git/hooks
    subprocess.run(["ap", "prek", "install", "--prepare-hooks"], check=True)


def update_prek(data_update: dict):
    from afterpython.utils import deep_merge

    pre_commit_path = ap.paths.afterpython_path / ".pre-commit-config.yaml"
    if not pre_commit_path.exists():
        raise FileNotFoundError(
            f".pre-commit-config.yaml not found at {pre_commit_path}"
        )
    existing_data = read_yaml(pre_commit_path)
    existing_data = deep_merge(existing_data, data_update)
    write_yaml(pre_commit_path, existing_data)
    install_prek()


def init_prek():
    pre_commit_path = ap.paths.afterpython_path / ".pre-commit-config.yaml"
    if pre_commit_path.exists():
        print(f".pre-commit-config.yaml already exists at {pre_commit_path}")
        return
    pre_commit_template_path = (
        ap.paths.templates_path / "pre-commit-config-template.yaml"
    )
    shutil.copy(pre_commit_template_path, pre_commit_path)
    print(f"Created {pre_commit_path}")
    install_prek()


def _hook_ids(repo) -> list[str]:
    return [hook["id"] for hook in repo.get("hooks", [])]


def sync_hooks():
    """Keep each tool's hooks only when its config file in afterpython/ exists (see TOOL_HOOKS).

    Declining a tool during `ap init` (or its setup being skipped) removes its hooks,
    so that declining e.g. ruff means no ruff checks on commit (and in CI),
    and `ap init <tool>` adds them back from the template.
    """
    pre_commit_path = ap.paths.afterpython_path / ".pre-commit-config.yaml"
    if not pre_commit_path.exists():
        return
    data = read_yaml(pre_commit_path)
    repos = data["repos"]
    template_repos = read_yaml(
        ap.paths.templates_path / "pre-commit-config-template.yaml"
    )["repos"]
    template_ids = [_hook_ids(repo) for repo in template_repos]

    changed = False
    for tool, (config_file, hook_id) in TOOL_HOOKS.items():
        ids = [_hook_ids(repo) for repo in repos]
        index = next((i for i, repo_ids in enumerate(ids) if hook_id in repo_ids), None)
        has_config = (ap.paths.afterpython_path / config_file).exists()
        if has_config and index is None:
            template_index = next(
                i for i, repo_ids in enumerate(template_ids) if hook_id in repo_ids
            )
            # same place as in the template: before the next template repo that's present
            later_ids = template_ids[template_index + 1 :]
            insert_at = next(
                (i for i, repo_ids in enumerate(ids) if repo_ids in later_ids),
                len(repos),
            )
            repos.insert(insert_at, template_repos[template_index])
            print(f"Added the {tool} hooks to {pre_commit_path}")
            changed = True
        elif not has_config and index is not None:
            del repos[index]
            print(
                f"Removed the {tool} hooks from {pre_commit_path} (no afterpython/{config_file})"
            )
            changed = True
    if changed:
        write_yaml(pre_commit_path, data)
