[MyST]: https://mystmd.org
[MyST Markdown]: https://mystmd.org/guide/quickstart
[Table of Contents]: https://mystmd.org/guide/table-of-contents


# Quickstart

## Installation and Initialization

```bash
# install afterpython as a dev dependency
uv add --dev afterpython

# initialize afterpython/
ap init
```

---
## Writing Content
After running `ap init`, the `afterpython/` directory is created and you can start writing content right away.

The structure of `afterpython/` is as follows:
- `afterpython/doc/`
- `afterpython/blog/`
- `afterpython/tutorial/`
- `afterpython/example/`
- `afterpython/guide/`

All these subdirectories are initialized by `myst init` (see [MyST Markdown]), with a default `index.md` file for each content type.

For example, to start writing documentation of your project, run `ap doc` to start the development server for the `afterpython/doc/` directory, then create a new `.md` or `.ipynb` file in `afterpython/doc/`.

You can then view the documentation at `http://localhost:3000/` (or the port specified by `ap doc --port`).

Similarly, you can start the development server for other content types by running `ap blog`, `ap tutorial`, `ap example`, or `ap guide`, and then create `.md` or `.ipynb` files in the corresponding directory.

:::{seealso}
To learn more about how to arrange your content, see [Table of Contents] or a [Quick Guide about myst.yml](walkthrough/myst_yml.md).
:::

---
## Project Website
A project website is basically a website that serves as the **homepage for your project**.

It sits on top of your content, including documentation, blog posts, tutorials, examples, and guides.

You can run `ap dev` to start the development server for the project website to see how everything looks and works together.

Note that this server is **independent** from the development servers for your content — you need to run `ap doc` to start another server for the *Documentation tab* in your website to work.

For convenience, you can run `ap dev --all` to start the development server for all content types and the project website at once, so that you don't need to run `ap doc`, `ap blog`, `ap tutorial`, `ap example`, or `ap guide` separately.

:::{tip} Standard Workflow
The typical workflow is:
- Run `ap doc` (and other content types) and start writing content
- When finished, run `ap dev --all` to see what the final project website looks like
:::

See [](project_website.md)  for more details.

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


:::{important} `afterpython` badge
To support `afterpython`, consider adding this badge [![afterpython](https://afterpython.org/shield.svg)](https://afterpython.org) to your python project's `README.md` by writing:

`[![afterpython](https://afterpython.org/shield.svg)](https://afterpython.org)`
:::

:::{seealso} Quick Guide to MyST
:class: dropdown
[MyST] is the document engine that powers `afterpython`. You may want to read the [Quick Guide to MyST](myst.md) to understand what you can do with it before writing content.
:::
