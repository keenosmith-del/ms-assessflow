"""Lock installed runtime dependency closure separately from development tooling."""

import tomllib
from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

project = tomllib.loads(Path("backend/pyproject.toml").read_text())
pending = [Requirement(x) for x in project["project"]["dependencies"]]
visited = set()
versions = {}
while pending:
    requirement = pending.pop()
    name = canonicalize_name(requirement.name)
    key = (name, tuple(sorted(requirement.extras)))
    if key in visited:
        continue
    visited.add(key)
    package = distribution(name)
    versions[name] = package.version
    for value in package.requires or []:
        child = Requirement(value)
        if not child.marker or any(
            child.marker.evaluate({"extra": extra})
            for extra in ["", *requirement.extras]
        ):
            pending.append(child)
Path("backend/requirements.runtime.lock").write_text(
    "\n".join(f"{name}=={version}" for name, version in sorted(versions.items())) + "\n"
)
