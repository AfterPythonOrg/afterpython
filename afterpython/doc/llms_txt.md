[llms.txt]: https://llmstxt.org/

# llms.txt

[llms.txt] is a markdown file at a website's root (`/llms.txt`) that serves as a curated catalog of the site's content for AI agents (Claude, GPT, etc.) to consume. Think of it as a sitemap, but written for LLMs instead of search engines.

> You can find the llms.txt of `afterpython`'s website here: <https://afterpython.afterpython.org/llms.txt>

---
## Role in `afterpython`

`afterpython` generates **one single `llms.txt`** for the whole project website — there is no per-content-type variant. Its job is to act as **the catalog** that points an AI agent at every published page in one place.

The file is built into `afterpython/_website/static/llms.txt` during `ap build` and served at `/llms.txt` on the deployed project website.

---
## What's in it

- **Header**: your project's `README.md`, copied in verbatim — with badges (shields, download counters, etc.) automatically stripped from the header zone.
- **Sections**: one `## ` per content type, in this order:
  - Documentation, Tutorials, Guides, Examples, Blog
  - empty content types are skipped entirely
- **Section blurb**: pulled from `project.description` in `afterpython/{type}/myst.yml`.
- **Entries**: one link per page, with the page's `abstract:` (from frontmatter) appended if set.

Example of a section:

```markdown
## Documentation

> Documentation for the AfterPython toolkit

- [Quickstart](/doc/quickstart.md): get afterpython running in 5 minutes
- [Concepts](/doc/concepts.md)
- [Project Website](/doc/project-website.md)
```
