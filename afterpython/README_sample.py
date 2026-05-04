import marimo

__generated_with = "0.23.4"
app = marimo.App()


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


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


if __name__ == "__main__":
    app.run()
