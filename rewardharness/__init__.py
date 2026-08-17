"""Public package for RewardHarness with lazy top-level exports."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from rewardharness._version import __version__

if TYPE_CHECKING:
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
    "__version__",
]

_EXPORTS = {
    "EvaluationExample": ("rewardharness.domain", "EvaluationExample"),
    "EvaluationResult": ("rewardharness.domain", "EvaluationResult"),
    "Library": ("rewardharness.library", "Library"),
    "LibraryRepository": ("rewardharness.library", "LibraryRepository"),
    "Preference": ("rewardharness.domain", "Preference"),
    "RewardHarnessConfig": ("rewardharness.config", "RewardHarnessConfig"),
    "ScoreCard": ("rewardharness.domain", "ScoreCard"),
    "SelfEvolutionPipeline": ("rewardharness.evolution.pipeline", "SelfEvolutionPipeline"),
    "SubAgent": ("rewardharness.evaluation.engine", "SubAgent"),
}


def __getattr__(name: str) -> Any:
    """Load public objects on first access to keep metadata imports lightweight."""
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute = target
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
