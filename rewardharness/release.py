"""Release identity and tag validation utilities."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass

from rewardharness._version import __version__

_PACKAGE_VERSION = re.compile(r"^(?P<base>\d+\.\d+\.\d+)(?:(?P<stage>a|b|rc)(?P<number>\d+))?$")
_TAG_VERSION = re.compile(r"^v(?P<base>\d+\.\d+\.\d+)(?:-(?P<stage>a|b|rc)(?P<number>\d+))?$")


def package_version_to_tag(version: str) -> str:
    """Convert a PEP 440 package version to the repository tag convention."""
    match = _PACKAGE_VERSION.fullmatch(version)
    if match is None:
        raise ValueError(f"Unsupported package version: {version!r}")
    suffix = ""
    if match["stage"]:
        suffix = f"-{match['stage']}{match['number']}"
    return f"v{match['base']}{suffix}"


def tag_to_package_version(tag: str) -> str:
    """Convert a repository release tag to its PEP 440 package version."""
    match = _TAG_VERSION.fullmatch(tag)
    if match is None:
        raise ValueError(f"Unsupported release tag: {tag!r}")
    suffix = ""
    if match["stage"]:
        suffix = f"{match['stage']}{match['number']}"
    return f"{match['base']}{suffix}"


@dataclass(frozen=True, slots=True)
class ReleaseIdentity:
    """Canonical identifiers shared by Git, GitHub Releases, and PyPI."""

    package_version: str
    tag: str
    prerelease: bool
    pypi_url: str

    @classmethod
    def current(cls) -> ReleaseIdentity:
        match = _PACKAGE_VERSION.fullmatch(__version__)
        if match is None:
            raise RuntimeError(f"Invalid package version: {__version__!r}")
        tag = package_version_to_tag(__version__)
        return cls(
            package_version=__version__,
            tag=tag,
            prerelease=bool(match["stage"]),
            pypi_url=f"https://pypi.org/project/rewardharness/{__version__}/",
        )

    def validate_tag(self, tag: str) -> None:
        actual_version = tag_to_package_version(tag)
        if actual_version != self.package_version:
            raise ValueError(
                f"Tag {tag!r} resolves to {actual_version!r}; "
                f"package version is {self.package_version!r}"
            )

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-tag", metavar="TAG")
    args = parser.parse_args(argv)
    identity = ReleaseIdentity.current()
    if args.check_tag:
        identity.validate_tag(args.check_tag)
    print(json.dumps(identity.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
