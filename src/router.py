"""Compatibility wrapper for :mod:`rewardharness.evaluation.router`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.evaluation.router import ROUTING_PROMPT, Router

__all__ = ["ROUTING_PROMPT", "Router"]
