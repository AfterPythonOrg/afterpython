![GitHub stars](https://img.shields.io/github/stars/AfterPythonOrg/afterpython?style=social)
![PyPI downloads](https://img.shields.io/pypi/dm/afterpython)
[![PyPI](https://img.shields.io/pypi/v/afterpython.svg)](https://pypi.org/project/afterpython)
![PyPI - Support Python Versions](https://img.shields.io/pypi/pyversions/afterpython)
![Discussions](https://img.shields.io/badge/Discussions-Let's%20Chat-green)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/AfterPythonOrg/afterpython)


# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```bash
# create a new project in the current directory
npx sv create

# create a new project in my-app
npx sv create my-app
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.
