"""Compatibility wrapper for :mod:`rewardharness.clients.gemini`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.clients.gemini import call_gemini, get_client

__all__ = ["call_gemini", "get_client"]
