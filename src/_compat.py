"""Shared deprecation notice for legacy modules."""

from __future__ import annotations

import warnings


def warn_legacy(module: str) -> None:
    warnings.warn(
        f"{module} is deprecated; import from rewardharness instead",
        DeprecationWarning,
        stacklevel=3,
    )
