#!/usr/bin/env python3
"""Compatibility entry point for ``rewardharness benchmark``."""

import sys

from rewardharness.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["benchmark", *sys.argv[1:]]))
