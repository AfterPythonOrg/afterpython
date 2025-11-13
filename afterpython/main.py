# import atexit

from afterpython.cli import afterpython_group


def exit_cli():
    """Application Exitpoint."""
    print("Cleanup actions here...")


def run_cli() -> None:
    """Application Entrypoint."""
    # atexit.register(exit_cli)
    afterpython_group(obj={})


def run_pcu() -> None:
    """Entrypoint for 'pcu' command (alias for 'ap update deps')."""
    from afterpython.cli.commands.update import dependencies
    dependencies()


if __name__ == "__main__":
    run_cli()
