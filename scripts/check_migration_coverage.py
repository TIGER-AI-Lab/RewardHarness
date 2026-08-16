#!/usr/bin/env python3
"""Verify that the v0.2 migration accounts for every baseline file."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "migration-manifest.json"


def _git(*args: str) -> list[str]:
    output = subprocess.check_output(["git", *args], cwd=ROOT, text=True)
    return [line for line in output.splitlines() if line]


def main() -> int:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    baseline = document["baseline_sha"]
    baseline_files = set(_git("ls-tree", "-r", "--name-only", baseline))
    manifest_files = {entry["old_path"] for entry in document["entries"]}
    if manifest_files != baseline_files:
        missing = sorted(baseline_files - manifest_files)
        extra = sorted(manifest_files - baseline_files)
        raise SystemExit(f"migration manifest mismatch; missing={missing}, extra={extra}")

    changed_files = set(_git("diff", "--no-renames", "--name-only", baseline))
    unchanged = sorted(baseline_files - changed_files)
    if unchanged:
        raise SystemExit(f"baseline files without a semantic migration: {unchanged}")

    if document["tracked_files"] != len(baseline_files):
        raise SystemExit("tracked_files count does not match the baseline tree")
    print(f"migration coverage: {len(baseline_files)}/{len(baseline_files)} baseline files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
