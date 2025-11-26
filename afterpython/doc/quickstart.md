[MyST]: https://mystmd.org
[MyST Markdown]: https://mystmd.org/guide/quickstart
[Table of Contents]: https://mystmd.org/guide/table-of-contents


# Quickstart

## Install & Initialize

```bash
# install afterpython as a dev dependency
uv add --dev afterpython

# initialize afterpython/
ap init
```

After running `ap init`, the `afterpython/` directory is created and you can start writing content right away.

The structure of `afterpython/` is as follows:
- `afterpython/doc/`
- `afterpython/blog/`
- `afterpython/tutorial/`
- `afterpython/example/`
- `afterpython/guide/`

:::{note} Default Branch Protection Rules
Default branch protection rules can be created by running `ap init-branch-rules`. See [](package_maintenance/ci_cd.md#branch-protection-rules) for more details.
:::


---
## Project Website
A project website is basically a website that serves as the **homepage for your project**.

It aggregates and presents all your content in one place, including documentation, blog posts, tutorials, examples, and how-to guides.

To **set the logo and favicon** for the project website, put your `logo.svg` and `favicon.svg` in the `afterpython/static/` directory.

See [](project_website.md)  for more details.

---
## Develop

### Starting Development Servers

AfterPython provides two ways to work with content:

1. **Project Website Only** - Run `ap dev` to start the development server for your project website.

2. **Individual Content Development** - Run `ap dev` with flags to work on specific content types:
   - `ap dev --doc` - Documentation
   - `ap dev --blog` - Blog posts
   - `ap dev --tutorial` - Tutorials
   - `ap dev --example` - Examples
   - `ap dev --guide` - Guides
   - `ap dev --all` - Everything at once (all content types + project website)

When using flags, a MyST development server starts for that specific content folder (e.g., `afterpython/doc/`), allowing you to write and preview content in `.md` or `.ipynb` files with live reload.

### Content Organization

All content folders in `afterpython/` (e.g., `afterpython/doc/`, `afterpython/blog/`) are initialized by `myst init` (see [MyST Markdown]), and **each** has a default `index.md` file and a `myst.yml` file for configuration.

:::{seealso}
To learn more about how to arrange your content in the content folders, see [Table of Contents] or a [Quick Guide about myst.yml](myst.md).
:::

---
## Build & Preview
To build for production, run `ap build`.

run `ap preview` to preview the production build of the project website.


---
## Deploy
A `deploy.yml` file is created in the `.github/workflows/` directory during initialization, which is a GitHub Actions workflow for deploying the project website to GitHub Pages.

By default, it will be triggered for deployment when you push any content changes to the `main` branch. If you don't want this, you can:
- write content in a different branch, or
- disable the workflow by commenting out the `on: push` section in the `deploy.yml` file

*[MyST] is the document engine that powers `afterpython`. You may want to read the [Quick Guide to MyST](myst.md) to understand what you can do with it before writing content.*

---
:::{important} `afterpython` badge
To support `afterpython`, consider adding this badge [![afterpython](https://afterpython.org/shield.svg)](https://afterpython.org) to your python project's `README.md` by writing:

`[![afterpython](https://afterpython.org/shield.svg)](https://afterpython.org)`
:::
