"""Compatibility wrapper for :mod:`rewardharness.evaluation.metrics`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.evaluation.metrics import (
    compute_kpair_accuracy,
    evaluate_prediction,
)

__all__ = ["compute_kpair_accuracy", "evaluate_prediction"]
