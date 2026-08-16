#!/usr/bin/env python3
"""Verify that the ImagenHub schema migration preserved every rating value."""

from __future__ import annotations

import hashlib
from pathlib import Path

EXPECTED_SHA256 = {
    "rater1.tsv": "28f43928555944f49b4e47f4cadd41f4aa41f709dfd39f98236dc65f95fa13bf",
    "rater2.tsv": "7f1996d7f33d38b84258c79352d573bb811e838feab451eb5f321108f137eaa5",
    "rater3.tsv": "96d53658b1a7f38a703ed4a836e98ec6e8c2b6a9fd6f3d618be8930113bcf864",
}


def project_v1(path: Path) -> bytes:
    """Remove the additive schema column and reproduce the v1 byte layout."""
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        columns = line.split("\t")
        if len(columns) < 3:
            raise ValueError(f"{path}:{line_number}: expected at least three columns")
        if line_number == 1 and columns[1] != "schema_version":
            raise ValueError(f"{path}: missing schema_version column")
        if line_number > 1 and columns[1] != "1":
            raise ValueError(f"{path}:{line_number}: unsupported schema version {columns[1]!r}")
        rows.append("\t".join([columns[0], *columns[2:]]))
    return ("\n".join(rows) + "\n").encode()


def main() -> int:
    data_dir = Path(__file__).resolve().parent.parent / "vanilla" / "imagenhub_data"
    for filename, expected in EXPECTED_SHA256.items():
        actual = hashlib.sha256(project_v1(data_dir / filename)).hexdigest()
        if actual != expected:
            raise SystemExit(f"rating projection changed for {filename}: {actual} != {expected}")
        print(f"{filename}: preserved ({actual})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
