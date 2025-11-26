# Roadmap

```{warning}
This roadmap is tentative and subject to change
```

- integrate with `pdoc` for API reference generation
- convert blog posts to format compatible with medium.com and substack.com
- AI chatbot like kapa.ai using WebLLM
- full-text search engine using pagefind
- incremental build, only build changed content (for `ap dev`)
- github dependabot
    - update the versions in github workflows (e.g. `ci.yml`, not `pyproject.toml` coz `pcu` handles it already)
- integrate with `git-cliff` for changelog generation
- integrate with `pixi`, supports `conda install`
- supports docs built by different engines? e.g. Sphix, MkDocs
- update `afterpython` itself using `ap update afterpython`
    - it merges the new defaults in a newer version of `afterpython` into your project
    - very difficult, need to create an interactive UX to show the diffs and let the user choose to merge or not
- support python 3.14
