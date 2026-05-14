"""Unit tests for Library class."""

import json
import os
import pytest
from unittest.mock import MagicMock, patch

from src.library import Library


class TestLibrarySkills:
    def test_add_skill(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("color-check", "Check color consistency", "## Color Check\nVerify colors match.")

        assert "color-check" in lib.registry
        assert lib.registry["color-check"]["type"] == "skill"
        skill_path = tmp_library / "skills" / "color-check" / "SKILL.md"
        assert skill_path.exists()

    def test_get_skill(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("color-check", "Check color consistency", "## Color Check\nVerify colors match.")

        skill = lib.get_skill("color-check")
        assert skill["name"] == "color-check"
        assert skill["description"] == "Check color consistency"
        assert "Color Check" in skill["content"]

    def test_update_skill(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("color-check", "Check color consistency", "Original content")
        lib.update_skill("color-check", "Updated content", new_description="Updated description")

        skill = lib.get_skill("color-check")
        assert "Updated content" in skill["content"]
        assert skill["description"] == "Updated description"

    def test_update_skill_preserves_description(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("color-check", "Original desc", "Original content")
        lib.update_skill("color-check", "Updated content")  # no new_description

        skill = lib.get_skill("color-check")
        assert skill["description"] == "Original desc"

    def test_get_nonexistent_skill(self, tmp_library):
        lib = Library(str(tmp_library))
        with pytest.raises(KeyError):
            lib.get_skill("nonexistent")

    def test_update_nonexistent_skill(self, tmp_library):
        lib = Library(str(tmp_library))
        with pytest.raises(KeyError):
            lib.update_skill("nonexistent", "content")


class TestLibraryTools:
    def test_add_tool(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_tool(
            "tool-ocr", "Extract text from images",
            "You are an OCR tool. Return JSON.",
            {"images": "list[base64_str]", "query": "str"},
            {"text": "str", "confidence": "float"},
            "## Tool: OCR\nExtracts text."
        )

        assert "tool-ocr" in lib.registry
        assert lib.registry["tool-ocr"]["type"] == "tool"

    def test_get_tool(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_tool(
            "tool-ocr", "Extract text from images",
            "You are an OCR tool.",
            {"images": "list[base64_str]"}, {"text": "str"},
            "## Tool: OCR\nExtracts text."
        )

        tool = lib.get_tool("tool-ocr")
        assert tool["name"] == "tool-ocr"
        assert tool["system_prompt"] == "You are an OCR tool."

    def test_update_tool_system_prompt(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_tool(
            "tool-ocr", "Extract text", "Original prompt",
            {"images": "list"}, {"text": "str"},
            "## OCR Tool body"
        )
        lib.update_tool("tool-ocr", "Updated prompt")

        tool = lib.get_tool("tool-ocr")
        assert tool["system_prompt"] == "Updated prompt"
        # Body should be unchanged
        content = lib.get_full_content("tool-ocr")
        assert "OCR Tool body" in content

    def test_call_tool_via_vllm_api(self, tmp_library, mock_vllm_client):
        """call_tool must use OpenAI API (vLLM), NOT subprocess."""
        lib = Library(str(tmp_library))
        lib.add_tool(
            "tool-ocr", "Extract text",
            "You are an OCR tool. Return JSON.",
            {"images": "list"}, {"text": "str"},
            "## OCR"
        )

        mock_pool = MagicMock()
        mock_pool.next.return_value = "http://localhost:8000/v1"

        # Mock openai.OpenAI
        mock_vllm_client.chat.completions.create.return_value.choices[0].message.content = \
            json.dumps({"text": "Hello", "confidence": 0.95})

        with patch("src.library.openai.OpenAI", return_value=mock_vllm_client):
            result = lib.call_tool("tool-ocr", {"images": ["base64data"], "query": "read text"}, mock_pool)

        assert result["text"] == "Hello"
        assert result["confidence"] == 0.95
        mock_vllm_client.chat.completions.create.assert_called_once()


class TestLibraryShared:
    def test_empty_library_summaries(self, tmp_library):
        lib = Library(str(tmp_library))
        summaries = lib.get_all_summaries()
        assert summaries == {"skills": [], "tools": []}

    def test_get_all_summaries(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("skill-1", "Skill one", "content 1")
        lib.add_tool("tool-1", "Tool one", "prompt", {}, {}, "body")

        summaries = lib.get_all_summaries()
        assert len(summaries["skills"]) == 1
        assert len(summaries["tools"]) == 1
        assert summaries["skills"][0]["name"] == "skill-1"
        assert summaries["tools"][0]["name"] == "tool-1"

    def test_get_full_content(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("test-skill", "Test", "## Full Content\nWith details.")
        content = lib.get_full_content("test-skill")
        assert "Full Content" in content
        assert "With details" in content

    def test_registry_persistence(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("persistent-skill", "Persists", "content")

        # Create new Library instance from same dir
        lib2 = Library(str(tmp_library))
        assert "persistent-skill" in lib2.registry
        skill = lib2.get_skill("persistent-skill")
        assert skill["description"] == "Persists"

    def test_get_full_content_nonexistent(self, tmp_library):
        lib = Library(str(tmp_library))
        with pytest.raises(KeyError):
            lib.get_full_content("nonexistent")
