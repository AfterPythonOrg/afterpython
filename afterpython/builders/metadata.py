import json
import tomllib

from pyproject_metadata import StandardMetadata

from afterpython.const.paths import BUILD_PATH


def convert_paths():
    '''
    Convert paths in "description" field (README.md) in metadata.json to use the new paths in the build output.
    e.g. convert ./afterpython/static/image.png to static/image.png
    '''
    # Read metadata.json
    with open(BUILD_PATH / "metadata.json", "r") as f:
        metadata = json.load(f)
        markdown_text = metadata['description']
    
    # Replace with the correct paths
    updated_markdown = markdown_text.replace('./afterpython/static/', '/')
    
    # Write back to metadata.json
    metadata['description'] = updated_markdown
    with open(BUILD_PATH / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("Completed path conversion in metadata.json")


def build_metadata():
    '''Build metadata.json using pyproject.toml'''
    # Read and parse pyproject.toml
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)

    # Create metadata object
    metadata = StandardMetadata.from_pyproject(pyproject_data)

    # Write to metadata.json
    with open(BUILD_PATH / "metadata.json", "w") as f:
        json.dump(metadata.as_json(), f, indent=2)

    convert_paths()
