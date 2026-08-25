#!/usr/bin/env python3
"""Verify that the ImagenHub schema migration preserved every rating value."""

from __future__ import annotations

import hashlib
from pathlib import Path

EXPECTED_SHA256 = {
    "rater1.tsv": "b448a8c3888343fa8005d1718c387ae01cce711c63db40a9a2b1e1f1bc2c72a7",
    "rater2.tsv": "f34a846b94f54010a40ccca81a19f662a46fcfb1a6928efb06253ed301d474b3",
    "rater3.tsv": "9819c24d467cd09d496b791d7e30188addae3c4a949bc4def2aa95ad0e49dffa",
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

# Release review: RewardHarness v0.4.1 (2026-08-26).
