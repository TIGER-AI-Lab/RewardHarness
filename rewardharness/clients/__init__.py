"""Model-client and endpoint primitives."""

from __future__ import annotations

from rewardharness.clients.endpoints import EndpointPool
from rewardharness.clients.gemini import call_gemini, get_client
from rewardharness.clients.protocols import ChatModelClient, TextModelClient

__all__ = ["ChatModelClient", "EndpointPool", "TextModelClient", "call_gemini", "get_client"]

# Release review: RewardHarness v0.4.1 (2026-08-26).
