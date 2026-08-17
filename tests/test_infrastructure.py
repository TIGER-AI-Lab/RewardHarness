"""Tests for typed infrastructure, resource paths, and checkpoint helpers."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from rewardharness.cli import build_parser
from rewardharness.clients import gemini
from rewardharness.clients.endpoints import EndpointPool
from rewardharness.config import BenchmarkConfig, EvolutionConfig, RewardHarnessConfig
from rewardharness.domain import Preference, ScoreCard
from rewardharness.evaluation.engine import SubAgent
from rewardharness.evolution.pipeline import SelfEvolutionPipeline
from rewardharness.library import Library
from rewardharness.paths import default_library_path, score_guidelines_path


def test_endpoint_pool_round_robin_and_normalization():
    pool = EndpointPool(endpoints=["http://one.test/v1/", "https://two.test/v1"])
    assert pool.size == 2
    assert pool.next() == "http://one.test/v1"
    assert pool.next() == "https://two.test/v1"
    assert pool.next() == "http://one.test/v1"
    assert pool.all() == ["http://one.test/v1", "https://two.test/v1"]


def test_endpoint_pool_reads_comments_and_rejects_invalid_urls(tmp_path):
    endpoint_file = tmp_path / "endpoints.txt"
    endpoint_file.write_text("# comment\n\nhttp://localhost:8000/v1\n")
    assert EndpointPool(endpoints_file=str(endpoint_file)).size == 1
    with pytest.raises(ValueError, match="Invalid endpoint"):
        EndpointPool(endpoints=["localhost:8000"])
    with pytest.raises(ValueError, match="No endpoints"):
        EndpointPool(endpoints=[])
    with pytest.raises(ValueError, match="either endpoints"):
        EndpointPool()


def test_config_yaml_upgrade_and_validation(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("gemini:\n  model: test-model\nevolution:\n  train_n: 2\n  val_n: 1\n")
    config = RewardHarnessConfig.from_yaml(path)
    assert config.schema_version == 2
    assert config.gemini.model == "test-model"
    with pytest.raises(ValueError, match="Unsupported"):
        RewardHarnessConfig.from_mapping({"schema_version": 99})
    with pytest.raises(ValueError, match="mapping"):
        path.write_text("- not\n- a\n- mapping\n")
        RewardHarnessConfig.from_yaml(path)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"train_dataset": "TIGER-Lab/EditReward-Bench"}, "Benchmark data"),
        ({"train_n": 0}, "must be positive"),
        ({"batch_concurrent": 0}, "must be positive"),
        ({"explore_margin": 1.1}, "must be in"),
        ({"prune_every_n": -1}, "cannot be negative"),
    ],
)
def test_evolution_config_rejects_invalid_values(overrides, message):
    with pytest.raises(ValueError, match=message):
        EvolutionConfig(**overrides)


def test_benchmark_config_rejects_nonpositive_workers():
    with pytest.raises(ValueError, match="must be positive"):
        BenchmarkConfig(max_workers=0)


@pytest.mark.parametrize("value", ["A", "a", " A "])
def test_preference_normalization(value):
    assert Preference.parse(value) is Preference.A


def test_domain_validation_failures():
    with pytest.raises(ValueError, match="Unsupported preference"):
        Preference.parse("left")
    with pytest.raises(ValueError, match="integer"):
        ScoreCard(True, 2, 3, 4)
    with pytest.raises(ValueError, match="positive"):
        SubAgent(None, None, max_retries=0)


def test_packaged_resource_paths_exist():
    assert (default_library_path() / "registry.json").is_file()
    assert (score_guidelines_path() / "template1_instruction_following.md").is_file()


def test_cli_reports_package_version(capsys):
    with pytest.raises(SystemExit) as raised:
        build_parser().parse_args(["--version"])
    assert raised.value.code == 0
    assert capsys.readouterr().out.strip() == "rewardharness 0.2.0"


def test_gemini_text_and_candidate_fallback(monkeypatch):
    direct = SimpleNamespace(text="direct", candidates=[])
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_kwargs: direct))
    monkeypatch.setattr(gemini, "get_client", lambda: client)
    assert gemini.call_gemini("hello", model="test") == "direct"

    class Response:
        def __init__(self):
            self.candidates = [
                SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(text="candidate")]))
            ]

        @property
        def text(self):
            raise ValueError("partial")

    client.models.generate_content = lambda **_kwargs: Response()
    assert gemini.call_gemini("hello", model="test") == "candidate"


def test_gemini_rejects_empty_response(monkeypatch):
    response = SimpleNamespace(text="", candidates=[])
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_kwargs: response))
    monkeypatch.setattr(gemini, "get_client", lambda: client)
    with pytest.raises(ValueError, match="Empty response"):
        gemini.call_gemini("hello", model="empty-model")


def test_pipeline_data_helpers_preserve_position_invariance():
    pipeline = object.__new__(SelfEvolutionPipeline)
    image = Image.new("RGB", (1, 1), "white")
    prepared = pipeline._prepare_examples(
        [
            {
                "source_image": image,
                "left_image": image,
                "right_image": image,
                "instruction": "edit",
                "vote_type": "leftvote",
            }
        ]
    )
    assert prepared[0]["gt"] == "A"
    swapped = pipeline._augment_with_swaps(prepared)
    assert swapped[1]["gt"] == "B"
    assert swapped[1]["edited_A"] == prepared[0]["edited_B"]
    assert pipeline._map_vote_type("RIGHTVOTE") == "B"
    assert pipeline._map_vote_type("unknown") == "tie"


def test_checkpoint_v1_and_v2_loading(tmp_path):
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    (library_dir / "registry.json").write_text("{}")
    pipeline = object.__new__(SelfEvolutionPipeline)
    pipeline.library = Library(str(library_dir))
    pipeline.checkpoint_dir = str(tmp_path / "checkpoints")

    checkpoint = Path(pipeline.checkpoint_dir) / "iter_2"
    (checkpoint / "skills" / "one").mkdir(parents=True)
    (checkpoint / "skills" / "one" / "SKILL.md").write_text("# one")
    (checkpoint / "metadata.json").write_text(json.dumps({"iteration": 2, "val_acc": 0.5}))
    registry = {
        "schema_version": 2,
        "library": {"id": "checkpoint", "status": "active"},
        "entries": {"one": {"kind": "skill", "description": "one", "path": "skills/one/SKILL.md"}},
    }
    (checkpoint / "registry.json").write_text(json.dumps(registry))
    metadata, snapshot = pipeline._load_checkpoint(str(checkpoint))
    assert metadata["iteration"] == 2
    assert snapshot["registry"]["one"]["type"] == "skill"
    assert pipeline.get_latest_checkpoint()[0] == 2
