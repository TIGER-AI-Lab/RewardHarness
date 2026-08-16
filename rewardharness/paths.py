"""Project and packaged-resource path resolution."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def default_library_path() -> Path:
    return Path(str(files("rewardharness").joinpath("resources").joinpath("library")))


def default_endpoints_path() -> Path:
    return PROJECT_ROOT / "configs" / "endpoints.txt"


def score_guidelines_path() -> Path:
    return Path(str(files("rewardharness").joinpath("resources").joinpath("score_guidelines")))
