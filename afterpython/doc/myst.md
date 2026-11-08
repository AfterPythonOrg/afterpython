[MyST Documentation]: https://mystmd.org
[MyST Specification]: https://mystmd.org/spec/
[MyST History]: https://mystmd.org/guide/background#what-is-the-myst-document-engine-and-myst-markdown
[MyST Overview]: https://mystmd.org/guide/overview
[Jupyter Notebook]: https://jupyter.org
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

### Notebook Cell Tags
You can add tags to notebook cells to control their behavior. For example, you can add the `hide-input` tag to a cell to hide the input of the cell.

*See [Notebook Cell Tags](https://mystmd.org/guide/notebook-configuration#tbl-notebook-cell-tags) for more details.*

### Molab Badge

If the [environment variable](references/environment_variables.md) `AP_MOLAB_BADGE` is set to `1`, `afterpython` automatically adds [molab] badges to Jupyter Notebooks during the build process.

:::{note}
[molab] is a cloud service by [Marimo] that supports running Jupyter Notebooks in the cloud. The badge lets users open your notebooks and run them in the cloud for free.
:::


---
## Marimo Notebook
You can also write content as [Marimo] notebooks (`.py` files). MyST can't read marimo notebooks directly, so during `ap build` and `ap dev`, `afterpython` converts each one to a Jupyter Notebook (`.ipynb`) next to it, and MyST renders that.

Each notebook **runs in its own environment**, built from the dependencies declared at the top of the file ([PEP 723](https://peps.python.org/pep-0723/)). Its outputs on the website are therefore **reproducible**: they don't depend on which machine or environment runs `ap build`.

:::{note} Requirements
marimo is an optional dependency of `afterpython`. Install it with `uv add --dev "afterpython[marimo]"`. [uv](https://docs.astral.sh/uv/) is also required, because it creates each notebook's environment.
:::

### Writing a Notebook
Create or open a notebook with marimo's `--sandbox` flag, so the packages you install while writing are added to the notebook's dependencies automatically:

```bash
marimo edit --sandbox afterpython/tutorial/getting_started.py
```

Write text in `mo.md(...)` cells. They become regular Markdown cells, so all MyST syntax works in them (directives, roles, math, cross-references):

````python
# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo", "polars"]
# ///
import marimo

app = marimo.App()


@app.cell
def _(mo):
    mo.md(r"""
    ---
    title: Getting Started
    date: 2026-11-01
    tags: [polars]
    ---

    :::{note}
    This is a MyST admonition inside a marimo notebook.
    :::
    """)
    return


@app.cell
def _():
    import marimo as mo
    import polars as pl

    return mo, pl


@app.cell
def _(pl):
    pl.DataFrame({"x": [1, 2, 3]})
    return
````

### Rules
- **If you use frontmatter, it goes in the first cell.** Frontmatter (`title`, `date`, `authors`, `tags`, `thumbnail`, ...) is optional: without it, the page title comes from the first `# Heading`. But blog posts usually need it, since the listing page shows each post's date, authors, tags and thumbnail. MyST only reads frontmatter from a notebook's first cell, so the `mo.md(...)` cell that holds it must be the first cell in the file, **above the `import marimo as mo` cell** that marimo creates by default. This is fine in marimo, which runs cells in dependency order, not file order. If the frontmatter cell is anywhere else, the build stops with an error.
- **One notebook type per content folder.** A content folder (e.g. `afterpython/tutorial/`) contains either marimo notebooks or Jupyter Notebooks, not both (`.md` files are fine in either). Mixing them stops the build. To switch a folder to marimo, convert its notebooks with `marimo convert notebook.ipynb -o notebook.py`.
- **Errors fail the build.** If a cell raises an error while the notebook runs, the build stops with the error, rather than publishing a page that shows a traceback.
- **Pages are static.** Outputs such as tables, plots and printed text are shown on the website, but interactive marimo widgets (`mo.ui.*`) don't work.

### Using Your Own Package
Notebooks often import the package they document. Because each notebook has its own environment, it must declare your package as a dependency. Point it at your local code so the notebook always uses your latest changes:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo", "your_package"]
#
# [tool.uv.sources]
# your_package = { path = "../..", editable = true }
# ///
```

`path` is relative to the notebook and points to your project root, which is `../..` for a notebook at `afterpython/tutorial/getting_started.py`. If you forget this, the build error shows the exact lines to add.

The notebook's environment installs your package **with all of its dependencies**, so it can be large (if your package depends on `afterpython`, for example, all of `afterpython` is installed too). The first run takes a while, and later runs reuse uv's cache.

### Generated Notebooks
- The generated `.ipynb` files are build outputs. Don't edit them, as they are overwritten on every build. The `.py` file is the only source.
- They aren't committed. `afterpython` adds `*.ipynb` and `__marimo__/` (marimo's cache) to the content folder's `.gitignore`, and removes those lines when the folder no longer has marimo notebooks.
- If your `myst.yml` lists files in `toc`, reference the generated notebook, e.g. `- file: getting_started.ipynb`.
- `ap clean` deletes them.
- `--execute` (in `ap build --execute` and `ap dev --execute`) only applies to Jupyter Notebooks. Marimo notebooks always run in their own environment.
- With `AP_MOLAB_BADGE=1`, the molab badge on a marimo notebook's page opens the `.py` file.

### Previewing with `ap dev`
The recommended workflow is to finish writing a notebook in `marimo edit --sandbox`, which already shows live outputs, and then run `ap dev` (e.g. `ap dev --tutorial`) to see it as a website page. `ap dev` only re-runs notebooks that changed since the last run.

You can also keep `ap dev` running while you edit: saving a `.py` file re-runs that notebook and updates its page. Since every save runs the whole notebook, this can be slow for long-running notebooks, and `ap dev` prints a warning when a re-run takes more than 10 seconds.


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

---
### Table of Contents (TOC)
The `toc` subsection under `project` in `myst.yml` defines how your content is organized.

You can run `myst init --write-toc` in your content directory (e.g., `afterpython/doc/`) to automatically generate a TOC based on your existing content.

*See [Table of Contents](https://mystmd.org/guide/table-of-contents) for more details.*

---
### authors.yml
When you run `ap init`, `afterpython` creates an `authors.yml` file in the `afterpython/` directory and syncs authors from `pyproject.toml`. This allows you to easily manage the authors of your project.

*See [Authorship](https://mystmd.org/guide/authorship#skip-to-frontmatter), you can add social media links to your authors in `authors.yml` (e.g. GitHub, X, etc.)*

---
#### Change Author at Page Level
By default, authors defined in `authors.yml` will all be used in `myst.yml` at the project level (see `project.authors` in `myst.yml`). However, you can override this behavior at the page level by adding the `authors` frontmatter at the top of your content (e.g. `doc/your_page.md`):
```markdown
---
authors:
- new_author_id_defined_in_authors_yml
---
```


:::{tip}
This entire documentation is written in MyST Markdown. You can click the "Edit this page" button in the top right corner to see the source code as an example of how to write content in MyST Markdown.
:::


---
## Synchronization
`ap sync` copies corresponding values from `pyproject.toml` and `afterpython.toml` into `authors.yml` and `myst.yml`.

For example, after updating authors in `pyproject.toml`, run `ap sync` to update `authors.yml` and your `myst.yml` files automatically.

You can also change `[company.name]` in `afterpython.toml` and run `ap sync` to update `venue.title` (set to the company name) in your `myst.yml` files.
