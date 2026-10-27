"""Inspect released RewardHarness files without importing or installing the package."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "checkout", type=Path, nargs="?", default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    report = {}
    for relative in ("rewardharness/resources/library", "examples/seed_library"):
        base = (args.checkout / relative).resolve()
        document = json.loads((base / "registry.json").read_text(encoding="utf-8"))
        if document.get("schema_version") != 2:
            raise SystemExit("Expected the pinned schema-v2 registry.")
        entries = []
        for name, entry in sorted(document["entries"].items()):
            path = (base / entry["path"]).resolve()
            if base not in path.parents or not path.is_file():
                raise SystemExit("Missing or out-of-library file: " + name)
            entries.append(
                {
                    "name": name,
                    "kind": entry["kind"],
                    "path": entry["path"],
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        report[relative] = {
            "schema_version": document["schema_version"],
            "counts": dict(sorted(Counter(e["kind"] for e in entries).items())),
            "entries": entries,
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
