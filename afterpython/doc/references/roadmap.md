# Roadmap

```{warning}
This roadmap is tentative and subject to change
```

- AI chatbot like kapa.ai using WebLLM
- incremental build, only build changed content (for `ap dev`)
- integrate with `git-cliff` for changelog generation
- supports docs built by different engines? e.g. Sphix, MkDocs
- support google analytics
- update `afterpython` itself using `ap update afterpython`
    - it merges the new defaults in a newer version of `afterpython` into your project
    - very difficult, need to create an interactive UX to show the diffs and let the user choose to merge or not
- add type checker using `ty`
- support python 3.14
- integrate with `pixi`, supports `conda install`
- support testing across multiple os in ci.yml based on `platforms` set in `pixi.toml`?
