"""Compatibility wrapper for :mod:`rewardharness.evolution.pipeline`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.evolution.pipeline import (
    SelfEvolutionPipeline,
    image_to_base64,
)

__all__ = ["SelfEvolutionPipeline", "image_to_base64"]
