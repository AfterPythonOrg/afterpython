# VIBE-CODED
import re
import subprocess

from git import Repo

from afterpython.utils import has_gh


def get_git_user_config() -> dict | None:
    """Get Git user configuration (name and email)."""
    try:
        # Get the repo
        repo = Repo(search_parent_directories=True)

        # Access git config
        reader = repo.config_reader()

        # Get user name and email
        name = reader.get_value("user", "name", default=None)
        email = reader.get_value("user", "email", default=None)

        if not name or not email:
            return None

        return {"name": name, "email": email}
    except Exception:
        return None


def get_github_url() -> str | None:
    """Get GitHub repository URL from git remote origin."""
    try:
        # Get the repo
        repo = Repo(search_parent_directories=True)

        # Get origin remote URL
        if "origin" not in repo.remotes:
            return None

        remote_url = repo.remotes.origin.url
        # Verify it's a GitHub URL
        if "github.com" not in remote_url:
            return None

        # Convert SSH format to HTTPS format
        # git@github.com:user/repo.git -> https://github.com/user/repo
        if remote_url.startswith("git@github.com:"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")

        # Remove .git suffix if present
        remote_url = re.sub(r"\.git$", "", remote_url)

        return remote_url

    except (ImportError, Exception):
        # GitPython not installed or not in a git repo
        return None


def is_gh_authenticated():
    """Guide user through GitHub authentication."""
    if not has_gh():
        print("""
╭─────────────────────────────────────────╮
│  GitHub CLI Required                    │
╰─────────────────────────────────────────╯

Install it:
  • macOS:   brew install gh
  • Linux:   https://github.com/cli/cli/releases
  • Windows: https://cli.github.com/

        """)
        return False

    result = subprocess.run(["gh", "auth", "status"], capture_output=True, check=False)

    if result.returncode != 0:
        print("""
╭─────────────────────────────────────────╮
│  GitHub Authentication Required         │
╰─────────────────────────────────────────╯

Please authenticate with GitHub:

    gh auth login

        """)
        return False

    return True


def get_github_username() -> str | None:
    """Get authenticated username via gh CLI."""
    if not has_gh():
        return None

    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# TODO: use gh's token for pygithub to get repo issues
# def get_repo_issues(owner: str, repo: str) -> list[dict]:
