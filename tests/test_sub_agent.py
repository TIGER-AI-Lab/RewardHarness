"""Unit tests for SubAgent."""

import json
import pytest
from unittest.mock import MagicMock, patch, call

from src.sub_agent import SubAgent, BASE_INSTRUCTIONS_NO_TOOLS, TOOL_INSTRUCTIONS, FALLBACK_ANSWER


class TestSubAgent:
    @pytest.fixture
    def mock_library(self, tmp_library):
        from src.library import Library
        lib = Library(str(tmp_library))
        return lib

    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        pool.next.return_value = "http://localhost:8000/v1"
        return pool

    @pytest.fixture
    def sub_agent(self, mock_library, mock_pool):
        return SubAgent(library=mock_library, endpoint_pool=mock_pool)

    def test_direct_answer_no_tools(self, sub_agent):
        """SubAgent returns answer directly without tool calls."""
        answer_json = json.dumps({
            "preference": "A",
            "score_A_instruction": 4, "score_A_quality": 3,
            "score_B_instruction": 2, "score_B_quality": 2,
            "reasoning": "A follows instruction better"
        })
        vllm_output = f'<think>Comparing images</think>\n<answer>{answer_json}</answer>'

        with patch("src.sub_agent.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value.choices = [MagicMock()]
            mock_client.chat.completions.create.return_value.choices[0].message.content = vllm_output
            MockOpenAI.return_value = mock_client

            result = sub_agent.evaluate("src_b64", "a_b64", "b_b64", "add text", "")

        assert result["preference"] == "A"
        assert result["score_A_instruction"] == 4
        assert "chain" in result

    def test_tool_call_then_answer(self, sub_agent, mock_library, mock_pool):
        """SubAgent calls tool, gets obs, then answers."""
        # Add a tool to the library
        mock_library.add_tool("tool-ocr", "OCR", "You are OCR", {}, {}, "## OCR")

        tool_call_output = '<think>Need OCR</think>\n<tool>{"name": "tool-ocr", "images": ["b64"], "query": "read"}</tool>'
        answer_json = json.dumps({
            "preference": "B",
            "score_A_instruction": 2, "score_A_quality": 2,
            "score_B_instruction": 4, "score_B_quality": 3,
            "reasoning": "B has correct text"
        })
        answer_output = f'<think>OCR shows B correct</think>\n<answer>{answer_json}</answer>'

        call_count = [0]
        def mock_create(**kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            if call_count[0] == 0:
                resp.choices[0].message.content = tool_call_output
            else:
                resp.choices[0].message.content = answer_output
            call_count[0] += 1
            return resp

        with patch("src.sub_agent.OpenAI") as MockVLLM:
            mock_vllm = MagicMock()
            mock_vllm.chat.completions.create.side_effect = mock_create
            MockVLLM.return_value = mock_vllm

            with patch.object(mock_library, "call_tool", return_value={"text": "Hello", "confidence": 0.9}) as mock_call_tool:
                result = sub_agent.evaluate("src", "a", "b", "add text", "")

        assert result["preference"] == "B"
        mock_call_tool.assert_called_once()

    def test_tool_parse_extracts_json(self, sub_agent):
        """<tool> tag content is correctly parsed as JSON."""
        from src.sub_agent import SubAgent
        tool_text = '<tool>{"name": "tool-detect", "images": ["abc"], "query": "find objects"}</tool>'
        sa = sub_agent
        parsed = sa._parse_tool_call(tool_text)
        assert parsed["name"] == "tool-detect"
        assert parsed["images"] == ["abc"]

    def test_answer_parse_extracts_json(self, sub_agent):
        """<answer> tag content is correctly parsed."""
        answer_text = '<answer>{"preference":"tie","score_A_instruction":3,"score_A_quality":3,"score_B_instruction":3,"score_B_quality":3,"reasoning":"equal"}</answer>'
        parsed = sub_agent._parse_answer(answer_text)
        assert parsed["preference"] == "tie"
        assert parsed["score_A_instruction"] == 3

    def test_fallback_on_no_answer(self, sub_agent):
        """Returns fallback when SubAgent never outputs <answer>."""
        with patch("src.sub_agent.OpenAI") as MockVLLM:
            mock_vllm = MagicMock()
            mock_vllm.chat.completions.create.return_value.choices = [MagicMock()]
            mock_vllm.chat.completions.create.return_value.choices[0].message.content = "<think>I'm confused</think>"
            MockVLLM.return_value = mock_vllm

            result = sub_agent.evaluate("src", "a", "b", "test", "")

        assert result["preference"] == "tie"
        assert result["score_A_instruction"] == 2

    def test_max_tool_calls_limit(self, sub_agent, mock_library):
        """SubAgent stops after MAX_TOOL_CALLS tool invocations."""
        mock_library.add_tool("tool-test", "Test", "test prompt", {}, {}, "## Test")

        tool_output = '<tool>{"name": "tool-test", "images": [], "query": "test"}</tool>'

        with patch("src.sub_agent.OpenAI") as MockVLLM:
            mock_vllm = MagicMock()
            mock_vllm.chat.completions.create.return_value.choices = [MagicMock()]
            mock_vllm.chat.completions.create.return_value.choices[0].message.content = tool_output
            MockVLLM.return_value = mock_vllm

            with patch.object(mock_library, "call_tool", return_value={"result": "ok"}):
                result = sub_agent.evaluate("src", "a", "b", "test", "")

        assert result["preference"] == "tie"  # fallback

    def test_empty_context_pure_reasoning(self, sub_agent):
        """With empty skill_context, SubAgent uses pure Qwen reasoning."""
        answer_json = json.dumps({
            "preference": "A",
            "score_A_instruction": 3, "score_A_quality": 3,
            "score_B_instruction": 2, "score_B_quality": 2,
            "reasoning": "A better"
        })

        with patch("src.sub_agent.OpenAI") as MockVLLM:
            mock_vllm = MagicMock()
            mock_vllm.chat.completions.create.return_value.choices = [MagicMock()]
            mock_vllm.chat.completions.create.return_value.choices[0].message.content = f'<answer>{answer_json}</answer>'
            MockVLLM.return_value = mock_vllm

            result = sub_agent.evaluate("src", "a", "b", "test", "")  # empty context

        assert result["preference"] == "A"

    def test_tool_failure_returns_error_obs(self, sub_agent, mock_library):
        """When tool call fails, error is returned as <obs>."""
        mock_library.add_tool("tool-fail", "Fail", "fail prompt", {}, {}, "## Fail")

        call_count = [0]
        def mock_create(**kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            if call_count[0] == 0:
                resp.choices[0].message.content = '<tool>{"name": "tool-fail", "images": [], "query": "test"}</tool>'
            else:
                answer = json.dumps({"preference": "A", "score_A_instruction": 3, "score_A_quality": 3, "score_B_instruction": 2, "score_B_quality": 2, "reasoning": "ok"})
                resp.choices[0].message.content = f'<answer>{answer}</answer>'
            call_count[0] += 1
            return resp

        with patch("src.sub_agent.OpenAI") as MockVLLM:
            mock_vllm = MagicMock()
            mock_vllm.chat.completions.create.side_effect = mock_create
            MockVLLM.return_value = mock_vllm

            with patch.object(mock_library, "call_tool", side_effect=Exception("tool broke")):
                result = sub_agent.evaluate("src", "a", "b", "test", "")

        # Should still get an answer after error obs
        assert result["preference"] == "A"
