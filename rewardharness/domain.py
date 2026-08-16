"""Typed domain objects shared across evaluation and evolution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Preference(str, Enum):
    """Supported pairwise preferences."""

    A = "A"
    B = "B"
    TIE = "tie"

    @classmethod
    def parse(cls, value: str) -> Preference:
        normalized = value.strip()
        if normalized.lower() == "tie":
            return cls.TIE
        try:
            return cls(normalized.upper())
        except ValueError as exc:
            raise ValueError(f"Unsupported preference: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class ScoreCard:
    """Instruction-following and visual-quality scores for both candidates."""

    a_instruction: int
    a_quality: int
    b_instruction: int
    b_quality: int

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 4:
                raise ValueError(f"{name} must be an integer in [1, 4], got {value!r}")


@dataclass(frozen=True, slots=True)
class EvaluationExample:
    """One source image, two edited candidates, and their instruction."""

    source_img: str
    edited_a: str
    edited_b: str
    prompt: str
    group_id: str | int
    ground_truth: Preference | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> EvaluationExample:
        ground_truth = value.get("gt")
        return cls(
            source_img=str(value["source_img"]),
            edited_a=str(value["edited_A"]),
            edited_b=str(value["edited_B"]),
            prompt=str(value["prompt"]),
            group_id=value["group_id"],
            ground_truth=Preference.parse(str(ground_truth)) if ground_truth is not None else None,
        )


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Validated evaluator output including the full reasoning chain."""

    preference: Preference
    scores: ScoreCard
    reasoning: str
    chain: str = ""

    def to_legacy_dict(self) -> dict[str, Any]:
        return {
            "preference": self.preference.value,
            "score_A_instruction": self.scores.a_instruction,
            "score_A_quality": self.scores.a_quality,
            "score_B_instruction": self.scores.b_instruction,
            "score_B_quality": self.scores.b_quality,
            "reasoning": self.reasoning,
            "chain": self.chain,
        }
