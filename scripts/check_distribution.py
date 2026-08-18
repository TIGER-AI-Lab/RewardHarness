#!/usr/bin/env python3
"""Validate the exact contents and metadata of release distributions."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from email.message import Message
from email.parser import BytesParser
from email.policy import default
from pathlib import Path, PurePosixPath
from typing import NoReturn

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def _fail(message: str) -> NoReturn:
    raise SystemExit(f"distribution check failed: {message}")


def _validate_paths(names: set[str], archive: str) -> None:
    unsafe = sorted(
        name
        for name in names
        if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
    )
    if unsafe:
        _fail(f"{archive} contains unsafe paths: {unsafe}")


def _metadata(raw: bytes, archive: str) -> Message:
    message = BytesParser(policy=default).parsebytes(raw)
    required = {
        "Name": "rewardharness",
        "Requires-Python": ">=3.10",
        "License-Expression": "Apache-2.0",
        "Description-Content-Type": "text/markdown",
    }
    for field, expected in required.items():
        if message[field] != expected:
            _fail(f"{archive} {field} is {message[field]!r}, expected {expected!r}")
    classifiers = set(message.get_all("Classifier", []))
    if "Typing :: Typed" not in classifiers:
        _fail(f"{archive} does not declare inline typing support")
    project_urls = {value.split(",", 1)[0].strip() for value in message.get_all("Project-URL", [])}
    expected_urls = {"Homepage", "Documentation", "Repository", "Changelog", "Issues", "Paper"}
    if missing := expected_urls - project_urls:
        _fail(f"{archive} is missing project URLs: {sorted(missing)}")
    return message


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from rewardharness.release import ReleaseIdentity

    identity = ReleaseIdentity.current()
    wheel = DIST / f"rewardharness-{identity.package_version}-py3-none-any.whl"
    sdist = DIST / f"rewardharness-{identity.package_version}.tar.gz"
    expected_artifacts = {wheel, sdist}
    actual_artifacts = (
        {path for path in DIST.iterdir() if path.is_file()} if DIST.is_dir() else set()
    )
    if actual_artifacts != expected_artifacts:
        unexpected = sorted(path.name for path in actual_artifacts - expected_artifacts)
        missing = sorted(path.name for path in expected_artifacts - actual_artifacts)
        _fail(f"artifact set mismatch; missing={missing}, unexpected={unexpected}")

    dist_info = f"rewardharness-{identity.package_version}.dist-info"
    with zipfile.ZipFile(wheel) as zip_archive:
        wheel_names = set(zip_archive.namelist())
        _validate_paths(wheel_names, wheel.name)
        wheel_metadata = _metadata(zip_archive.read(f"{dist_info}/METADATA"), wheel.name)
    required_wheel = {
        "rewardharness/py.typed",
        "rewardharness/resources/library/registry.json",
        "rewardharness/resources/score_guidelines/template1_instruction_following.md",
        "rewardharness/resources/score_guidelines/template2_visual_quality.md",
        f"{dist_info}/entry_points.txt",
    }
    missing_wheel = required_wheel - wheel_names
    if missing_wheel:
        _fail(f"{wheel.name} is missing runtime files: {sorted(missing_wheel)}")
    forbidden_prefixes = ("tests/", "scripts/", "examples/", "vanilla/")
    leaked = sorted(name for name in wheel_names if name.startswith(forbidden_prefixes))
    if leaked:
        _fail(f"{wheel.name} contains non-runtime files: {leaked}")

    sdist_root = f"rewardharness-{identity.package_version}"
    with tarfile.open(sdist, "r:gz") as tar_archive:
        sdist_names = {member.name for member in tar_archive.getmembers()}
        _validate_paths(sdist_names, sdist.name)
        member = tar_archive.getmember(f"{sdist_root}/PKG-INFO")
        extracted = tar_archive.extractfile(member)
        if extracted is None:
            _fail(f"{sdist.name} has an unreadable PKG-INFO")
        sdist_metadata = _metadata(extracted.read(), sdist.name)
    required_sdist = {
        f"{sdist_root}/README.md",
        f"{sdist_root}/CHANGELOG.md",
        f"{sdist_root}/CITATION.cff",
        f"{sdist_root}/LICENSE",
        f"{sdist_root}/rewardharness/py.typed",
        f"{sdist_root}/configs/default.yaml",
    }
    missing_sdist = required_sdist - sdist_names
    if missing_sdist:
        _fail(f"{sdist.name} is missing source files: {sorted(missing_sdist)}")

    for message, archive_name in (
        (wheel_metadata, wheel.name),
        (sdist_metadata, sdist.name),
    ):
        if message["Version"] != identity.package_version:
            _fail(
                f"{archive_name} version is {message['Version']!r}, "
                f"expected {identity.package_version!r}"
            )
    print(f"distribution artifacts: 2/2 valid for {identity.package_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
