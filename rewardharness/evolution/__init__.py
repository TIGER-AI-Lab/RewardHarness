"""Self-evolution orchestration services."""

from __future__ import annotations

from rewardharness.evolution.analyzer import ChainAnalyzer
from rewardharness.evolution.evolver import Evolver
from rewardharness.evolution.pipeline import SelfEvolutionPipeline

EvolutionPipeline = SelfEvolutionPipeline

__all__ = ["ChainAnalyzer", "EvolutionPipeline", "Evolver", "SelfEvolutionPipeline"]

# Release review: RewardHarness v0.4.1 (2026-08-26).
