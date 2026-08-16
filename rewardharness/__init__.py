"""Public package for RewardHarness."""

from rewardharness.config import RewardHarnessConfig
from rewardharness.domain import EvaluationExample, EvaluationResult, Preference, ScoreCard
from rewardharness.evaluation.engine import SubAgent
from rewardharness.evolution.pipeline import SelfEvolutionPipeline
from rewardharness.library import Library, LibraryRepository

__all__ = [
    "EvaluationExample",
    "EvaluationResult",
    "Library",
    "LibraryRepository",
    "Preference",
    "RewardHarnessConfig",
    "ScoreCard",
    "SelfEvolutionPipeline",
    "SubAgent",
]

__version__ = "0.2.0rc1"
