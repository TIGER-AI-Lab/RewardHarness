"""Validated application configuration and normalization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class GeminiConfig:
    model: str = "gemini-3.1-pro-preview"


@dataclass(frozen=True, slots=True)
class EvolutionConfig:
    train_dataset: str = "AgPerry/EditReward-Data-100"
    train_n: int = 60
    val_n: int = 40
    max_iterations: int = 5
    batch_concurrent: int = 128
    explore_margin: float = 0.075
    augment_swap: bool = True
    prune_every_n: int = 50
    seed: int = 42

    def __post_init__(self) -> None:
        if "EditReward-Bench" in self.train_dataset:
            raise ValueError("Benchmark data must NOT be used during evolution!")
        if self.train_n < 1 or self.val_n < 1 or self.max_iterations < 1:
            raise ValueError("train_n, val_n, and max_iterations must be positive")
        if self.batch_concurrent < 1:
            raise ValueError("batch_concurrent must be positive")
        if not 0 <= self.explore_margin <= 1:
            raise ValueError("explore_margin must be in [0, 1]")
        if self.prune_every_n < 0:
            raise ValueError("prune_every_n cannot be negative")


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    dataset: str = "TIGER-Lab/EditReward-Bench"
    max_workers: int = 128

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise ValueError("benchmark.max_workers must be positive")


@dataclass(frozen=True, slots=True)
class RewardHarnessConfig:
    """Top-level typed configuration."""

    schema_version: int = 2
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)
    model: Mapping[str, Any] = field(default_factory=dict)

    @staticmethod
    def _section(value: Mapping[str, Any], name: str) -> dict[str, Any]:
        section = value.get(name, {})
        if not isinstance(section, Mapping):
            raise ValueError(f"Configuration section {name!r} must be a mapping")
        return dict(section)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> RewardHarnessConfig:
        schema_version = int(value.get("schema_version", 1))
        if schema_version not in (1, 2):
            raise ValueError(f"Unsupported configuration schema_version: {schema_version}")
        return cls(
            schema_version=2,
            gemini=GeminiConfig(**cls._section(value, "gemini")),
            evolution=EvolutionConfig(**cls._section(value, "evolution")),
            benchmark=BenchmarkConfig(**cls._section(value, "benchmark")),
            model=cls._section(value, "model"),
        )

    @classmethod
    def coerce(cls, value: RewardHarnessConfig | Mapping[str, Any]) -> RewardHarnessConfig:
        """Return one canonical typed configuration from either supported input shape."""
        return value if isinstance(value, RewardHarnessConfig) else cls.from_mapping(value)

    @classmethod
    def from_yaml(cls, path: str | Path) -> RewardHarnessConfig:
        with Path(path).open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        if not isinstance(raw, Mapping):
            raise ValueError("Configuration root must be a mapping")
        return cls.from_mapping(raw)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the validated configuration to its schema-v2 mapping."""
        return asdict(self)

    def to_legacy_dict(self) -> dict[str, Any]:
        """Compatibility alias for callers written before the typed configuration API."""
        return self.to_dict()
