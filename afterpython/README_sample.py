# ruff: noqa

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.23.8",
#     "pfeed==0.0.8",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pfeed as pe

    return mo, pe


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Test
    """)
    return


@app.cell
def _():
    print("Hello AfterPython")
    return


@app.cell
async def _():
    import sys

    if sys.platform == "emscripten":
        import micropip

        await micropip.install(["polars", "pyarrow", "pyodide-http"])

        # avoid creating a thread in tqdm
        import tqdm

        tqdm.tqdm.monitor_interval = 0

        import pyodide_http

        pyodide_http.patch_all()

        # CORS proxy shim — public.bybit.com sends no CORS headers,
        # so route every httpx.get through a proxy that does.
        import httpx

        _orig_get = httpx.get
        PROXY = "https://pfeed-cors.lucky-water-569b.workers.dev/?url="

        def _proxied_get(url, *args, **kwargs):
            return _orig_get(PROXY + url, *args, **kwargs)

        httpx.get = _proxied_get
    return


@app.cell(hide_code=True)
def _(mo):
    mo.callout(
        mo.md(
            "**Demo mode.** This is `pfeed` running in WASM — core features "
            "are not fully supported. "
            "For full functionality, install locally:\n\n"
            "```\npip install pfeed[core]\n```\n"
            "Click **▶ Run all** (top right) to start. First run takes ~15s while Pyodide and dependencies load."
        ),
        kind="info",
    )
    return


@app.cell
def _(pe):
    bybit = pe.Bybit()
    feed = bybit.market_feed
    result = feed.download(
        product="BTC_USDT_PERP",
        resolution="1minute",
        start_date="2026-01-01",
        end_date="2026-01-01",
        storage_config=None,
    )
    df = result.data.collect()
    df
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
