[mystmd]: https://mystmd.org
[commitizen]: https://github.com/commitizen-tools/commitizen
[pre-commit]: https://github.com/pre-commit/pre-commit
[ruff]: https://github.com/astral-sh/ruff

# Concepts

## afterpython/ Folder
The `afterpython/` folder serves as a centralized location for both your project website content and maintenance tool configurations. It contains:

**Content directories:**
- `afterpython/doc/` - Documentation
- `afterpython/blog/` - Blog posts
- `afterpython/tutorial/` - Tutorials
- `afterpython/example/` - Examples
- `afterpython/guide/` - How-to Guides

**Configuration files:**
- `cz.toml` for [commitizen]
- `ruff.toml` for [ruff]
- `.pre-commit-config.yaml` for [pre-commit]
- `authors.yml` for [mystmd]
- `afterpython.toml` for `afterpython` itself

**Purpose:**

This structure serves two goals:

1. **Declutter the root directory** - Keeps maintenance-related configuration files separate from package code, making the project structure cleaner
2. **Provide sane defaults** - Comes pre-configured with sensible defaults for common maintenance tools like [commitizen], [pre-commit], and [ruff], so you can start using them immediately


---
## afterpython.toml
`afterpython.toml` is a configuration file for `afterpython`. Think of it as an extension of `pyproject.toml`, storing extra information about your project such as company name, company URL, project website URL, etc. Currently it only supports the following fields:

```toml
[company]
name = "Your Company Name"
url = "https://your-company.com"

[website]
url = "https://your-project-website.com"
favicon = "favicon.svg"
logo = "logo.svg"
logo_dark = "logo.svg"
thumbnail = "thumbnail.png"
```

---
## Content Types
- **Documentation** (`afterpython/doc/`) - Conceptual explanations on how the project works
- **Blog** (`afterpython/blog/`) - Project updates, announcements, and release notes
- **Tutorials** (`afterpython/tutorial/`) - Step-by-step learning guides
- **Examples** (`afterpython/example/`) - Real-world code examples/snippets
- **Guides** (`afterpython/guide/`) - Task-oriented how-to instructions
- **API Reference** (`afterpython/reference/`) - Auto-generated API documentation from docstrings
