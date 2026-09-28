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


def get_current_user_id() -> int | None:
    """
    Get the GitHub user ID of the currently authenticated user.

    Returns:
        User ID or None if error
    """
    if not is_gh_authenticated():
        return None

    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".id"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error fetching user ID: {result.stderr}")
        return None

    try:
        return int(result.stdout.strip())
    except ValueError:
        print("Error: Failed to parse user ID")
        return None


# TODO: use gh's token for pygithub to get repo issues
# def get_repo_issues(owner: str, repo: str) -> list[dict]:


def _git_output(*args: str) -> str | None:
    """Run a git command in the project root, return its stripped stdout or None on failure"""
    import afterpython as ap

    result = subprocess.run(
        ["git", *args],
        cwd=ap.paths.user_path,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def get_default_branch(remote: str = "origin") -> str | None:
    """Get the remote's default branch, e.g. "main" """
    # set by `git clone`, e.g. "origin/main"
    ref = _git_output(
        "symbolic-ref", "--quiet", "--short", f"refs/remotes/{remote}/HEAD"
    )
    if ref:
        return ref.removeprefix(f"{remote}/")
    # not set when the remote was added to an existing repo, ask the remote instead
    output = _git_output("ls-remote", "--symref", remote, "HEAD") or ""
    match = re.match(r"ref: refs/heads/(\S+)\s+HEAD", output)
    return match.group(1) if match else None


def check_release_branch(remote: str = "origin") -> str:
    """Return the current branch if releases are allowed from it:
    it's the remote's default branch and has all the remote's commits"""
    import click

    branch = _git_output("symbolic-ref", "--quiet", "--short", "HEAD")
    if branch is None:
        raise click.ClickException("Not on a branch (detached HEAD), can't release")
    default_branch = get_default_branch(remote)
    if default_branch is None:
        raise click.ClickException(
            f"Unable to find the default branch of remote '{remote}', check that it's reachable"
        )
    if branch != default_branch:
        raise click.ClickException(
            f"Releases are only allowed from '{default_branch}', current branch is '{branch}'"
        )
    # fetch (not pull) so nothing changes locally; the user decides how to bring in new commits
    if _git_output("fetch", "--quiet", remote, branch) is None:
        raise click.ClickException(f"Unable to fetch '{branch}' from '{remote}'")
    behind = _git_output("rev-list", "--count", f"HEAD..{remote}/{branch}")
    if behind and behind != "0":
        raise click.ClickException(
            f"'{remote}/{branch}' has {behind} commit(s) you don't have, run `git pull` first"
        )
    return branch
