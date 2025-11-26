import click


@click.command()
def init_branch_rules():
    """Create default branch protection rules for the current repository"""
    from afterpython.tools.branch_rules import create_default_branch_rules

    create_default_branch_rules()
