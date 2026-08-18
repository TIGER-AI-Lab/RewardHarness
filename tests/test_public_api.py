"""Contract tests for the canonical public API."""

from __future__ import annotations

import json

import pytest

from rewardharness.config import RewardHarnessConfig
from rewardharness.domain import EvaluationExample, EvaluationResult, Preference, ScoreCard
from rewardharness.evaluation.router import Router
from rewardharness.library import Library


def _config() -> dict:
    return {
        "gemini": {"model": "gemini-3.1-pro-preview"},
        "evolution": {"train_n": 80, "val_n": 20},
        "benchmark": {},
    }


def test_typed_config_round_trip():
    config = _config()
    typed = RewardHarnessConfig.from_mapping(config)
    assert typed.evolution.train_n == 80
    assert typed.to_legacy_dict()["gemini"]["model"] == "gemini-3.1-pro-preview"


@pytest.mark.parametrize("field,value", [("train_n", 0), ("batch_concurrent", 0)])
def test_typed_config_rejects_non_positive_evolution_values(field, value):
    config = _config()
    config["evolution"][field] = value
    with pytest.raises(ValueError):
        RewardHarnessConfig.from_mapping(config)


def test_domain_result_legacy_shape():
    result = EvaluationResult(
        preference=Preference.A,
        scores=ScoreCard(4, 3, 2, 1),
        reasoning="candidate A follows the instruction",
    )
    assert result.to_legacy_dict()["score_B_quality"] == 1


def test_evaluation_example_accepts_legacy_keys():
    example = EvaluationExample.from_mapping(
        {
            "source_img": "source",
            "edited_A": "a",
            "edited_B": "b",
            "prompt": "edit",
            "group_id": 7,
            "gt": "tie",
        }
    )
    assert example.ground_truth is Preference.TIE


def test_library_rejects_path_traversal(tmp_library):
    library = Library(str(tmp_library))
    with pytest.raises(ValueError, match="kebab-case"):
        library.add_skill("../escape", "bad", "bad")


def test_library_writes_v2_registry(tmp_library):
    library = Library(str(tmp_library))
    library.add_skill("safe-name", "safe", "# Safe")
    document = json.loads((tmp_library / "registry.json").read_text())
    assert document["schema_version"] == 2
    assert document["entries"]["safe-name"]["kind"] == "skill"


@pytest.mark.parametrize(
    "response",
    [
        "[]",
        '{"skills": "not-a-list", "tools": []}',
        '{"skills": [1], "tools": []}',
    ],
)
def test_router_rejects_invalid_json_shapes(response):
    assert Router._parse_response(response) is None


def test_router_deduplicates_valid_selections():
    parsed = Router._parse_response('{"skills": ["a", "a"], "tools": ["b", "b"]}')
    assert parsed == {"skills": ["a"], "tools": ["b"]}
