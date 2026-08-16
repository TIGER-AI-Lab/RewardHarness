"""Compatibility wrapper for :mod:`rewardharness.evolution.analyzer`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.evolution.analyzer import ANALYSIS_PROMPT, ChainAnalyzer

__all__ = ["ANALYSIS_PROMPT", "ChainAnalyzer"]
