"""
pcu = "pip check updates", similar to ncu (npm check updates in Node.js)
"""

from typing import TypedDict, NamedTuple, TypeAlias
import asyncio

from packaging.requirements import Requirement

from afterpython._paths import Paths


class Dependency(NamedTuple):
    min_version: str | None
    requirement: Requirement
    latest_version: str | None = None


DependencyName: TypeAlias = str
ExtrasName: TypeAlias = str
GroupName: TypeAlias = str
FakeCategoryName: TypeAlias = str
Dependencies = TypedDict(
    "Dependencies",
    {
        "dependencies": list[Dependency],
        "optional-dependencies": dict[ExtrasName, list[Dependency]],
        "dependency-groups": dict[GroupName, list[Dependency]],
    },
)
# add FakeCategoryName "fake_category" to "dependencies" to make all dependencies have the same structure
NormalizedDependencies = TypedDict(
    "NormalizedDependencies",
    {
        "dependencies": dict[FakeCategoryName, list[Dependency]],
        "optional-dependencies": dict[ExtrasName, list[Dependency]],
        "dependency-groups": dict[GroupName, list[Dependency]],
    },
)


def parse_min_version_from_requirement(req: Requirement) -> str | None:
    version = None
    if req.specifier:
        # req.specifier is like ">=8.3.0" or ">=1.0,<2.0"
        for spec in req.specifier:
            # spec.version gives you the version part
            version = spec.version
            break  # Use first one as "current version"
    return version


async def get_latest_versions(requirements: list[Requirement]) -> dict[str, str | None]:
    """Get latest versions for a list of dependencies from PyPI."""
    import httpx
    from afterpython.utils.pypi import fetch_pypi_json

    async def fetch_version(client: httpx.AsyncClient, package_name: str) -> str | None:
        """Fetch the latest version of a package from PyPI."""
        data = await fetch_pypi_json(client, package_name)
        return data["info"]["version"] if data else None

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [fetch_version(client, req.name) for req in requirements]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip([req.name for req in requirements], results, strict=False))


def get_dependencies(
    is_normalized: bool = True,
) -> Dependencies | NormalizedDependencies:
    """Get dependencies from pyproject.toml"""
    import tomllib
    from pyproject_metadata import StandardMetadata

    pyproject_path = Paths().pyproject_path
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
        metadata = StandardMetadata.from_pyproject(pyproject_data)
        # somehow pyproject_metadata didn't handle dependency-groups, so we need to convert it to type "Requirement"
        metadata.dependency_groups: dict[str, list[Requirement]] = {
            group_name: [Requirement(dep) for dep in dependencies]
            for group_name, dependencies in pyproject_data["dependency-groups"].items()
        }

    # Collect all unique requirements across all categories
    all_requirements = list(metadata.dependencies)
    for requirements in metadata.optional_dependencies.values():
        all_requirements.extend(requirements)
    for requirements in metadata.dependency_groups.values():
        all_requirements.extend(requirements)

    # Fetch ALL latest versions in ONE async call
    latest_versions = asyncio.run(get_latest_versions(all_requirements))

    dependencies = {
        "dependencies": [
            Dependency(
                min_version=parse_min_version_from_requirement(req),
                requirement=req,
                latest_version=latest_versions.get(req.name),
            )
            for req in metadata.dependencies
        ],
        "optional-dependencies": {
            extras_name: [
                Dependency(
                    min_version=parse_min_version_from_requirement(req),
                    requirement=req,
                    latest_version=latest_versions.get(req.name),
                )
                for req in requirements
            ]
            for extras_name, requirements in metadata.optional_dependencies.items()
        },
        "dependency-groups": {
            group_name: [
                Dependency(
                    min_version=parse_min_version_from_requirement(req),
                    requirement=req,
                    latest_version=latest_versions.get(req.name),
                )
                for req in requirements
            ]
            for group_name, requirements in metadata.dependency_groups.items()
        },
    }
    return normalize_dependencies(dependencies) if is_normalized else dependencies


def normalize_dependencies(dependencies: Dependencies) -> NormalizedDependencies:
    '''Add "fake_category" to "dependencies" to have the same structure as "optional-dependencies" and "dependency-groups"'''
    return {
        "dependencies": {"fake_category": dependencies["dependencies"]},
        "optional-dependencies": dependencies["optional-dependencies"],
        "dependency-groups": dependencies["dependency-groups"],
    }


def update_dependencies(dependencies: NormalizedDependencies):
    """Update dependency versions in pyproject.toml"""
    import tomlkit

    pyproject_path = Paths().pyproject_path
    with open(pyproject_path) as f:
        doc = tomlkit.parse(f.read())

    for dep_type in dependencies:
        # category = extras or group name
        for category, deps in dependencies[dep_type].items():
            if dep_type == "dependencies":
                doc_deps = doc["project"][dep_type]
            elif dep_type == "optional-dependencies":
                doc_deps = doc["project"][dep_type][category]
            elif dep_type == "dependency-groups":
                doc_deps = doc["dependency-groups"][category]
            else:
                raise ValueError(f"Invalid dependency type: {dep_type}")
            
            # Update in place
            # package = e.g. "click>=8.3.0"
            for i, (dep, package) in enumerate(zip(deps, doc_deps, strict=False)):
                if dep.requirement.name in package and dep.min_version and dep.latest_version and dep.min_version in package:
                    doc_deps[i] = package.replace(dep.min_version, dep.latest_version)
    
    with open(pyproject_path, 'w') as f:
        f.write(tomlkit.dumps(doc))
