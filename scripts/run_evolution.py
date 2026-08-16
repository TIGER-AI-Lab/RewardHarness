#!/usr/bin/env python3
"""Compatibility entry point for ``rewardharness evolve``."""

import sys

from rewardharness.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["evolve", *sys.argv[1:]]))
