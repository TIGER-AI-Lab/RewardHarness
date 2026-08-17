#!/usr/bin/env python3
"""Verify that release metadata agrees with the canonical package version."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

try:
    import tomllib
except ImportError:  # pragma: no cover - exercised by the Python 3.10 CI job
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from rewardharness.release import ReleaseIdentity

    identity = ReleaseIdentity.current()
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    if pyproject["project"]["name"] != "rewardharness":
        raise SystemExit("pyproject project name must be rewardharness")
    required_urls = {"Homepage", "Documentation", "Repository", "Changelog", "Issues", "Paper"}
    missing_urls = required_urls - pyproject["project"]["urls"].keys()
    if missing_urls:
        raise SystemExit(f"pyproject is missing project URLs: {sorted(missing_urls)}")
    version_source = pyproject["tool"]["setuptools"]["dynamic"]["version"]["attr"]
    if version_source != "rewardharness._version.__version__":
        raise SystemExit("pyproject must read the canonical _version module")
    citation_version = str(citation["version"])
    if citation_version != identity.tag.removeprefix("v"):
        raise SystemExit(
            f"CITATION.cff version {citation_version!r} does not match {identity.tag!r}"
        )
    if f"## [{citation_version}]" not in changelog:
        raise SystemExit(f"CHANGELOG.md has no release heading for {citation_version}")
    package_data = pyproject["tool"]["setuptools"]["package-data"]["rewardharness"]
    if "py.typed" not in package_data or not (ROOT / "rewardharness" / "py.typed").is_file():
        raise SystemExit("the PEP 561 py.typed marker must be packaged")
    print(
        f"release metadata: package={identity.package_version} "
        f"tag={identity.tag} citation={citation_version}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
