[PyPI]: https://pypi.org/
[Svelte]: https://svelte.dev/

# Project Website

> The project website for `afterpython` is created using `afterpython` itself. See the [**website**](https://afterpython.afterpython.org).

## Definition
On [PyPI], you typically see three urls under **Project Links**,
and they are defined in the `[project.urls]` section of `pyproject.toml`.
Most projects that are not backed by a company either omit the homepage field,
or reuse the documentation URL as the homepage, even though it already has its own link.
![PyPI homepage button](../static/homepage.png)

Here is where `afterpython` comes to the rescue:

It **automatically generates a project website that serves as the `homepage`** for every Python project,
allowing even small, resource-constrained projects to have a dedicated website.
Essentially, it **extends your documentation site into a fully featured website**.

---
## Architecture
:::{div}
:class: dark:hidden
![project website](../static/project_website.svg)
:::


:::{div}
:class: hidden dark:block
![project website dark](../static/project_website_dark.svg)
:::

inside `afterpython/` directory:
Blog/Tutorials/Examples
content types: doc, blog, tutorial, example, guide, etc.

use a full web ui framework ([Svelte]) to wrap the content and escape the scope of MyST

### API Reference
use pdoc
### FAQs
faq.yml
### Compatibility
support sphinx, mkdocs

---
## Built-in Features
- full-text search engine (Work in Progress)
- AI chatbot (Work in Progress)
### Google Analytics

---
## Website Template Update
`ap update website`
Caveat: This will overwrite the existing project website template.
### Customization and Styling
can use LLM to code any web components in [Svelte]
