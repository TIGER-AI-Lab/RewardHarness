"""Evaluation services and metrics."""

from rewardharness.evaluation.engine import SubAgent
from rewardharness.evaluation.metrics import compute_kpair_accuracy, evaluate_prediction
from rewardharness.evaluation.router import Router

EvaluationEngine = SubAgent

__all__ = [
    "EvaluationEngine",
    "Router",
    "SubAgent",
    "compute_kpair_accuracy",
    "evaluate_prediction",
]
