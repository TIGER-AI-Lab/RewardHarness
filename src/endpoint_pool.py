"""Compatibility wrapper for :mod:`rewardharness.clients.endpoints`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.clients.endpoints import EndpointPool

__all__ = ["EndpointPool"]
