from pathlib import Path


PROJ_NAME = Path(__file__).resolve().parents[1].name
MAIN_PATH = Path(__file__).resolve().parents[2]
AFTERPYTHON_PATH = MAIN_PATH / "afterpython"
WEBSITE_PATH = AFTERPYTHON_PATH / "_website"
BUILD_PATH = AFTERPYTHON_PATH / "_build"
STATIC_PATH = AFTERPYTHON_PATH / "static"
DOCS_PATH = AFTERPYTHON_PATH / "docs"