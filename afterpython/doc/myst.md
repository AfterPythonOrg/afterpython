[MyST Documentation]: https://mystmd.org
[MyST Specification]: https://mystmd.org/spec/
[MyST History]: https://mystmd.org/guide/background#what-is-the-myst-document-engine-and-myst-markdown
[MyST Overview]: https://mystmd.org/guide/overview
[Jupyter Notebook]: https://jupyter.org
[template]: https://github.com/AfterPythonOrg/project-website-template
[JupyterBook]: https://jupyterbook.org/stable/
[molab]: https://molab.marimo.io/
[Marimo]: https://marimo.io/

# Quick Guide to MyST

:::{attention}
This section serves as a quick guide to MyST. Quotes below are sourced from the [MyST Documentation], where you can find more comprehensive information.
:::


## What is MyST?
> MyST (Markedly Structured Text) is designed to create publication-quality, computational documents written entirely in Markdown. The main use case driving the development and design of MyST is [JupyterBook], which creates educational online textbooks and tutorials with Jupyter Notebooks and narrative content written in MyST.


### MyST Markdown vs Common Markdown
> MyST is a superset of CommonMark (a standard form of Markdown) and allows you to directly create “directives” and “roles” as extension points in the language. These extensions points are influenced by ReStructured Text (RST) and Sphinx -- pulling on the nomenclature and introducing additional standards where appropriate. directives are block-level extension points, like callout panels, tabs, figures or embedded charts; and roles are inline extension points, for components like references, citations, or inline math.

- **See [this](https://mystmd.org/guide/quickstart-myst-markdown) for a quick start guide to MyST Markdown's syntax.**
- See [MyST Specification] and [MyST History] for more details about what MyST is.


---
## Jupyter Notebook
The [MyST Document Engine][MyST Overview] can parse [Jupyter Notebook]s and render them as HTML. This means you can write content in both MyST Markdown and Jupyter Notebooks—`afterpython` will organize and render them together as part of your project website.

### Molab Badge

If the [environment variable](references/environment_variables.md) `AP_MOLAB_BADGE` is set to `1`, `afterpython` automatically adds [molab] badges to Jupyter Notebooks during the build process.

:::{note}
[molab] is a cloud service by [Marimo] that supports running Jupyter Notebooks in the cloud. The badge lets users open your notebooks and run them in the cloud for free.
:::


---
## myst.yml
`myst.yml` is a configuration file for MyST, and since `afterpython` uses MyST to build content, each directory (`doc/`, `blog/`, `tutorial/`, `example/`, and `guide/`) has its own `myst.yml` configuration file. This allows you to customize MyST's behavior per directory.

### Configuration Structure

A `myst.yml` file contains two main sections:

**`project`** — Project-level settings such as description, keywords, and GitHub URL.

*See [Frontmatter](https://mystmd.org/guide/frontmatter#available-frontmatter-fields) for all available options.*

**`site`** — Website-level settings such as template, site title, logo, and favicon.

*See [Site Options](https://mystmd.org/guide/website-templates#available-website-template-options) for all available options.*

:::{caution} Bug Report
Some settings in `myst.yml` may not work as expected, and you may need to report the bugs on [`mystmd` GitHub Issues](https://github.com/jupyter-book/mystmd/issues).

Please do **_NOT_** report `mystmd` bugs on `afterpython` repository.
:::

### Table of Contents (TOC)
The `toc` subsection under `project` in `myst.yml` defines how your content is organized.

You can run `myst init --write-toc` in your content directory (e.g., `afterpython/doc/`) to automatically generate a TOC based on your existing content.

*See [Table of Contents](https://mystmd.org/guide/table-of-contents) for more details.*

### authors.yml
When you run `ap init`, `afterpython` creates an `authors.yml` file in the `afterpython/` directory and syncs authors from `pyproject.toml`. This allows you to easily manage the authors of your project.

*See [Authorship](https://mystmd.org/guide/authorship#skip-to-frontmatter), you can add social media links to your authors in `authors.yml` (e.g. GitHub, X, etc.)*

#### Change Author at Page Level
By default, authors defined in `authors.yml` will all be used in `myst.yml` at the project level (see `project.authors` in `myst.yml`). However, you can override this behavior at the page level by adding the `authors` frontmatter at the top of your content (e.g. `doc/your_page.md`):
```markdown
---
authors:
- new_author_id_defined_in_authors_yml
---
```
