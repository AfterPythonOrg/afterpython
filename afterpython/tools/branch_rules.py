"""
Branch protection rules for AfterPython projects.
Uses gh CLI to create GitHub rulesets.
"""

import json
import subprocess
from copy import deepcopy

from afterpython.tools._git import is_gh_authenticated


DEFAULT_RULESET = {
    "name": "afterpython-default",  # The ruleset identifier in GitHub
    "target": "branch",  # This ruleset applies to branches (not tags)
    "enforcement": "active",  # Rules are enforced (vs "disabled" or "evaluate")
    "conditions": {  # Which branches this ruleset applies to
        "ref_name": {
            "include": ["refs/heads/main"],  # Only protect the 'main' branch
            "exclude": [],  # No exclusions
        }
    },
    "bypass_actors": [
        {
            "actor_id": 5,  # Repository admin role
            "actor_type": "RepositoryRole",
            "bypass_mode": "always",
        }
    ],
    "rules": [  # Array of protection rules
        # Rule 1: No Force Pushes
        {"type": "non_fast_forward"},  # Prevents git push --force
        # Rule 2: No Branch Deletion
        {"type": "deletion"},  # Prevents branch from being deleted
        # Rule 3: CI Status Checks
        {
            "type": "required_status_checks",
            "parameters": {
                "required_status_checks": [
                    {"context": "lint"},
                    {"context": "test"},
                    {"context": "build"},
                ],
                # The PR branch must be up to date with the base branch (main) before merging
                "strict_required_status_checks_policy": True,
            },
        },
    ],
}


def list_rulesets() -> list[dict] | None:
    """
    List existing rulesets for the current repository.

    Returns:
        List of rulesets or None if error
    """
    if not is_gh_authenticated():
        return None

    result = subprocess.run(
        ["gh", "api", "repos/{owner}/{repo}/rulesets"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error listing rulesets: {result.stderr}")
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Error: Failed to parse rulesets JSON")
        return None


def create_default_branch_rules(branch: str = "main") -> bool:
    if not is_gh_authenticated():
        return False

    # Check if ruleset already exists
    existing_rulesets = list_rulesets()
    if existing_rulesets:
        print(f"Ruleset '{DEFAULT_RULESET['name']}' already exists.")
        return False

    # Build payload
    payload = deepcopy(DEFAULT_RULESET)
    if branch != "main":
        payload["conditions"]["ref_name"]["include"] = [f"refs/heads/{branch}"]

    # Create ruleset
    result = subprocess.run(
        ["gh", "api", "-X", "POST", "repos/{owner}/{repo}/rulesets", "--input", "-"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error creating ruleset: {result.stderr}")
        return False

    print(f"✓ Created branch ruleset '{DEFAULT_RULESET['name']}' for {branch=}")
    return True
