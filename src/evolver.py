"""Compatibility wrapper for :mod:`rewardharness.evolution.evolver`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.evolution.evolver import (
    TOOL_VALIDATION_PROMPT,
    Evolver,
)

__all__ = ["TOOL_VALIDATION_PROMPT", "Evolver"]
