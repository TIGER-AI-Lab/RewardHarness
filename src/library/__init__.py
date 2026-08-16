"""Compatibility wrapper for :mod:`rewardharness.library`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.library import Library, LibraryRepository  # noqa: E402

__all__ = ["Library", "LibraryRepository"]
