"""
pcu = "pip check updates", similar to ncu (npm check updates in Node.js)
"""
from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict, NamedTuple, TypeAlias

if TYPE_CHECKING:
    from tomlkit.toml_document import TOMLDocument

import asyncio

from packaging.requirements import Requirement

from afterpython.version import Version


class Dependency(NamedTuple):
    requirement: Requirement
    min_version: Version | None
    max_version: Version | None = None
    latest_version: Version | None = None


DependencyName: TypeAlias = str
ExtrasName: TypeAlias = str
GroupName: TypeAlias = str
FakeCategoryName: TypeAlias = str
Dependencies = TypedDict(
    "Dependencies",
    {
        "dependencies": dict[FakeCategoryName, list[Dependency]],
        "optional-dependencies": dict[ExtrasName, list[Dependency]],
        "dependency-groups": dict[GroupName, list[Dependency]],
        "build-system": dict[str, list[Dependency]],
    },
)


def parse_min_max_versions_from_requirement(req: Requirement) -> dict[str, Version | None]:
    min_ver: Version | None = None
    max_ver: Version | None = None
    if req.specifier:
        # req.specifier is like ">=8.3.0" or ">=1.0,<2.0"
        versions = sorted(Version(spec.version) for spec in req.specifier)
        if len(versions) == 1:
            min_ver = versions[0]
        else:
            min_ver, max_ver = versions[0], versions[-1]
    return {
        'min_version': min_ver,
        'max_version': max_ver,
    }


async def get_latest_versions(requirements: list[Requirement]) -> dict[str, Version | None]:
    """Get latest versions for a list of dependencies from PyPI."""
    import httpx
    from afterpython.utils import fetch_pypi_json

    async def fetch_version(client: httpx.AsyncClient, package_name: str) -> Version | None:
        """Fetch the latest version of a package from PyPI."""
        data = await fetch_pypi_json(client, package_name)
        return Version(data["info"]["version"]) if data else None

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [fetch_version(client, req.name) for req in requirements]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip([req.name for req in requirements], results, strict=False))


def get_dependencies() -> Dependencies:
    """Get dependencies from pyproject.toml"""
    from afterpython._io.toml import read_pyproject

    doc: TOMLDocument = read_pyproject()
    dependencies = {
        'dependencies': list(doc['project'].get('dependencies', [])),
        'optional-dependencies': dict(doc['project'].get('optional-dependencies', {})),
        'dependency-groups': dict(doc.get('dependency-groups', {})),
        'build-system': dict(doc.get('build-system', {})),
    }
    # add "fake_category" to "dependencies" to have the same structure as "optional-dependencies" and "dependency-groups"
    dependencies['dependencies'] = {'fake_category': dependencies['dependencies']}
    # only keep the "requires" key
    if 'requires' in dependencies['build-system']:
        dependencies['build-system'] = {'requires': dependencies['build-system']['requires']}

    # convert all dependency strings to type "Requirement"
    for dep_type in dependencies:
        for category, deps in dependencies[dep_type].items():
            dependencies[dep_type][category] = [Requirement(dep) for dep in deps]
    
    # flatten the dependencies to a list of type "Requirement"
    all_reqs = [
        req for deps_dict in dependencies.values() 
        for req_list in deps_dict.values() 
        for req in req_list
    ]

    # Fetch ALL latest versions in ONE async call
    latest_versions = asyncio.run(get_latest_versions(all_reqs))

    # convert the requirements to type "Dependency"
    for dep_type in dependencies:
        for category, requirements in dependencies[dep_type].items():
            dependencies[dep_type][category] = [
                Dependency(
                    **parse_min_max_versions_from_requirement(req),
                    requirement=req,
                    latest_version=latest_versions.get(req.name)
                )
                for req in requirements
            ]

    return dependencies


def update_dependencies(dependencies: Dependencies):
    """Update dependency versions in pyproject.toml"""
    from afterpython._io.toml import read_pyproject, write_pyproject

    doc: TOMLDocument = read_pyproject()
    for dep_type in dependencies:
        # category = extras or group name
        for category, deps in dependencies[dep_type].items():
            if dep_type == "dependencies":
                doc_deps = doc["project"][dep_type]
            elif dep_type == "optional-dependencies":
                doc_deps = doc["project"][dep_type][category]
            elif dep_type in ["dependency-groups", "build-system"]:
                doc_deps = doc[dep_type][category]
            else:
                raise ValueError(f"Invalid dependency type: {dep_type}")
            
            # Update in place
            for i, (dep, package) in enumerate(zip(deps, doc_deps, strict=False)):
                package: str  # package = e.g. "click>=8.3.0"
                req: Requirement = dep.requirement
                min_ver = str(dep.min_version) if dep.min_version else None
                max_ver = str(dep.max_version) if dep.max_version else None
                latest_ver = str(dep.latest_version) if dep.latest_version else None
                if req.name in package and min_ver and latest_ver and min_ver in package:
                    doc_deps[i] = package.replace(min_ver, latest_ver)
                    if max_ver and dep.latest_version not in req.specifier:
                        doc_deps[i] = doc_deps[i].replace(max_ver, str(dep.max_version.next_breaking()))

    write_pyproject(doc)
