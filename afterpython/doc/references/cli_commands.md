# CLI Commands

:::{caution}
Since configuration files are stored in `afterpython/` rather than the root directory (where `pyproject.toml` lives), some tools that only search the root directory by default (e.g., [pre-commit]) require special handling. You have two options:

1. Use CLI commands wrapped by `ap` (e.g., `ap pre-commit ...`), which will automatically use the configuration files in `afterpython/` by default,
2. Move the configuration files to the root directory manually if you prefer using native commands directly (e.g., `pre-commit ...`)
:::
