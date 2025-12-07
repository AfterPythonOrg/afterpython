# Roadmap

```{warning}
This roadmap is tentative and subject to change
```

- add `FAQ` section to the project website and handle `faq.yml`
- add announcement section to the landing page
- integrate with `pdoc` for API reference generation
- convert blog posts to format compatible with medium.com and substack.com
- AI chatbot like kapa.ai using WebLLM
- full-text search engine using pagefind
- incremental build, only build changed content (for `ap dev`)
- integrate with `git-cliff` for changelog generation
- supports docs built by different engines? e.g. Sphix, MkDocs
- support google analytics
- update `afterpython` itself using `ap update afterpython`
    - it merges the new defaults in a newer version of `afterpython` into your project
    - very difficult, need to create an interactive UX to show the diffs and let the user choose to merge or not
- add type checker using `ty`
- support python 3.14
- `pcu` should support updating the versions in `pixi.toml`
- integrate with `pixi`, supports `conda install`
- support testing across multiple os in ci.yml based on `platforms` set in `pixi.toml`?
