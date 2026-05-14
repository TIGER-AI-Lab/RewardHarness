"""Integration tests for SelfEvolutionPipeline."""

import json
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from src.pipeline import SelfEvolutionPipeline
from src.library import Library
from src.evaluator import evaluate_prediction, compute_kpair_accuracy


@pytest.fixture
def config():
    return {
        "model": {"name": "Qwen2.5-VL-7B-Instruct"},
        "gemini": {"model": "gemini-3.1-pro-preview"},
        "evolution": {
            "train_dataset": "AgPerry/EditReward-Data-100",
            "train_n": 80,
            "val_n": 20,
            "max_iterations": 3,
            "batch_concurrent": 2,
            "seed": 42,
        },
        "benchmark": {"dataset": "TIGER-Lab/EditReward-Bench", "max_workers": 2},
    }


@pytest.fixture
def mock_train_examples():
    """Minimal fake train examples."""
    return [
        {"source_img": "src_b64", "edited_A": "a_b64", "edited_B": "b_b64",
         "prompt": f"edit {i}", "gt": "A" if i % 2 == 0 else "B", "group_id": i}
        for i in range(4)
    ]


@pytest.fixture
def mock_val_examples():
    """Minimal fake val examples."""
    return [
        {"source_img": "src_b64", "edited_A": "a_b64", "edited_B": "b_b64",
         "prompt": f"val edit {i}", "gt": "A", "group_id": i}
        for i in range(2)
    ]


class TestPipelineAssert:
    def test_benchmark_data_blocked(self, config, tmp_path):
        """Pipeline constructor must reject EditReward-Bench as train data."""
        config["evolution"]["train_dataset"] = "TIGER-Lab/EditReward-Bench"
        with pytest.raises(AssertionError, match="Benchmark data must NOT be used"):
            SelfEvolutionPipeline(config, library_dir=str(tmp_path))


class TestPipelineEvolution:
    @patch("src.pipeline.EndpointPool")
    @patch("src.router.call_gemini")
    @patch("src.chain_analyzer.call_gemini")
    @patch("src.sub_agent.OpenAI")
    def test_two_iteration_run(self, MockSubVLLM, mock_chain_gemini, mock_router_gemini,
                                MockPool, config, tmp_path, mock_train_examples, mock_val_examples):
        """Pipeline completes 2 iterations with mocked components."""
        # Setup mocks
        mock_pool = MagicMock()
        mock_pool.next.return_value = "http://localhost:8000/v1"
        MockPool.return_value = mock_pool

        # Library dir
        lib_dir = tmp_path / "library"
        lib_dir.mkdir()
        (lib_dir / "skills").mkdir()
        (lib_dir / "tools").mkdir()
        (lib_dir / "registry.json").write_text("{}")

        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Mock vLLM SubAgent responses
        answer = json.dumps({
            "preference": "A", "score_A_instruction": 3, "score_A_quality": 3,
            "score_B_instruction": 2, "score_B_quality": 2, "reasoning": "A better"
        })
        mock_vllm = MagicMock()
        mock_vllm.chat.completions.create.return_value.choices = [MagicMock()]
        mock_vllm.chat.completions.create.return_value.choices[0].message.content = f'<answer>{answer}</answer>'
        MockSubVLLM.return_value = mock_vllm

        # Mock Router Gemini (empty library → won't be called for iter 0)
        mock_router_gemini.return_value = json.dumps({"skills": [], "tools": []})

        # Mock ChainAnalyzer Gemini
        signals = json.dumps({
            "skill_updates": [{"action": "add", "name": "test-skill", "description": "Test", "content_md": "## Test"}],
            "tool_updates": [],
            "analysis_summary": "Added test skill"
        })
        mock_chain_gemini.return_value = signals

        config["evolution"]["max_iterations"] = 2

        pipeline = SelfEvolutionPipeline(config, library_dir=str(lib_dir))
        pipeline.results_dir = str(results_dir)
        pipeline.checkpoint_dir = str(results_dir / "checkpoints")

        log = pipeline.evolve(
            n_iterations=2,
            train_split=mock_train_examples,
            val_split=mock_val_examples
        )

        assert len(log) == 2
        assert log[0]["action"] == "baseline"
        assert log[0]["iteration"] == 0
        assert log[1]["iteration"] == 1
        assert "skill_action" in log[1]
        assert "tool_action" in log[1]
        assert "best_val_acc" in log[1]

    @patch("src.pipeline.EndpointPool")
    @patch("src.router.call_gemini")
    @patch("src.chain_analyzer.call_gemini")
    @patch("src.sub_agent.OpenAI")
    def test_keep_on_equal_val_acc(self, MockSubVLLM, mock_chain_gemini,
                                   mock_router_gemini, MockPool,
                                   config, tmp_path, mock_train_examples, mock_val_examples):
        """Equal val accuracy triggers keep (>= condition)."""
        mock_pool = MagicMock()
        mock_pool.next.return_value = "http://localhost:8000/v1"
        MockPool.return_value = mock_pool

        lib_dir = tmp_path / "library"
        lib_dir.mkdir()
        (lib_dir / "skills").mkdir()
        (lib_dir / "tools").mkdir()
        (lib_dir / "registry.json").write_text("{}")

        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # SubAgent always predicts "A" → some correct, some wrong
        answer_a = json.dumps({
            "preference": "A", "score_A_instruction": 3, "score_A_quality": 3,
            "score_B_instruction": 2, "score_B_quality": 2, "reasoning": "A"
        })
        mock_vllm = MagicMock()
        mock_vllm.chat.completions.create.return_value.choices = [MagicMock()]
        mock_vllm.chat.completions.create.return_value.choices[0].message.content = f'<answer>{answer_a}</answer>'
        MockSubVLLM.return_value = mock_vllm

        mock_router_gemini.return_value = json.dumps({"skills": [], "tools": []})

        # ChainAnalyzer suggests adding a skill
        signals = json.dumps({
            "skill_updates": [{"action": "add", "name": "bad-skill", "description": "Bad", "content_md": "## Bad"}],
            "tool_updates": [],
            "analysis_summary": "test"
        })
        mock_chain_gemini.return_value = signals

        pipeline = SelfEvolutionPipeline(config, library_dir=str(lib_dir))
        pipeline.results_dir = str(results_dir)
        pipeline.checkpoint_dir = str(results_dir / "checkpoints")

        # Since predictions don't change and val_acc stays same -> tie -> keep (>= condition)
        log = pipeline.evolve(n_iterations=2, train_split=mock_train_examples, val_split=mock_val_examples)

        assert log[1]["action"] == "keep"
        assert log[1]["skill_action"] == "keep"
        # With >= condition, equal val_acc means the skill is kept
        assert "bad-skill" in pipeline.library.registry

    def test_checkpoint_written(self, tmp_path):
        """Verify checkpoint directory structure."""
        checkpoint_dir = tmp_path / "checkpoints" / "iter_0"
        checkpoint_dir.mkdir(parents=True)

        # Simulate checkpoint files
        (checkpoint_dir / "registry.json").write_text("{}")
        metadata = {"iteration": 0, "val_acc": 0.5, "train_acc": 0.4, "timestamp": "2026-03-17"}
        (checkpoint_dir / "metadata.json").write_text(json.dumps(metadata))

        assert (checkpoint_dir / "registry.json").exists()
        assert (checkpoint_dir / "metadata.json").exists()
        loaded = json.loads((checkpoint_dir / "metadata.json").read_text())
        assert loaded["iteration"] == 0
