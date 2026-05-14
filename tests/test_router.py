"""Unit tests for Router."""

import json
import pytest
from unittest.mock import MagicMock, patch

from src.router import Router
from src.library import Library


class TestRouter:
    def test_empty_library_returns_empty(self, tmp_library):
        lib = Library(str(tmp_library))
        router = Router(lib)
        result = router.prepare_context("change the color to blue")
        assert result == ""

    def test_selects_skills_and_tools(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("color-check", "Check color consistency", "## Color\nCheck colors.")
        lib.add_tool("tool-ocr", "Read text", "OCR prompt", {}, {}, "## OCR\nReads text.")

        # Mock Gemini API to select both
        with patch("src.router.call_gemini") as mock_gemini:
            mock_gemini.return_value = json.dumps({"skills": ["color-check"], "tools": ["tool-ocr"]})

            router = Router(lib)
            result = router.prepare_context("add blue text overlay")

        assert "EVALUATION SKILLS" in result
        assert "Color" in result
        assert "AVAILABLE TOOLS" in result
        assert "OCR" in result

    def test_gemini_autonomous_selection_no_topk(self, tmp_library):
        """Router lets Gemini decide freely -- no fixed top-K parameter."""
        lib = Library(str(tmp_library))
        lib.add_skill("s1", "Skill 1", "Content 1")
        lib.add_skill("s2", "Skill 2", "Content 2")
        lib.add_skill("s3", "Skill 3", "Content 3")

        # Gemini selects all 3 -- no limit
        with patch("src.router.call_gemini") as mock_gemini:
            mock_gemini.return_value = json.dumps({"skills": ["s1", "s2", "s3"], "tools": []})

            router = Router(lib)
            result = router.prepare_context("test prompt")

        assert "Content 1" in result
        assert "Content 2" in result
        assert "Content 3" in result

    def test_small_library_uses_gemini(self, tmp_library):
        """Even small libraries go through Gemini routing."""
        lib = Library(str(tmp_library))
        lib.add_skill("s1", "Skill 1", "Content 1")

        with patch("src.router.call_gemini") as mock_gemini:
            mock_gemini.return_value = '{"skills": ["s1"], "tools": []}'
            router = Router(lib)
            result = router.prepare_context("test")

        mock_gemini.assert_called_once()
        assert "Content 1" in result

    def test_handles_invalid_json_response(self, tmp_library):
        """Large library with invalid Gemini response falls back gracefully."""
        lib = Library(str(tmp_library))
        for i in range(11):
            lib.add_skill(f"s{i}", f"Skill {i}", f"Content {i}")

        with patch("src.router.call_gemini") as mock_gemini:
            mock_gemini.return_value = "not valid json"

            router = Router(lib)
            result = router.prepare_context("test")

        assert result == ""  # graceful fallback

    def test_handles_fenced_json_response(self, tmp_library):
        """Router can parse JSON wrapped in markdown fences (fallback 1)."""
        lib = Library(str(tmp_library))
        lib.add_skill("s1", "Skill 1", "Content 1")

        with patch("src.router.call_gemini") as mock_gemini:
            mock_gemini.return_value = '```json\n{"skills": ["s1"], "tools": []}\n```'

            router = Router(lib)
            result = router.prepare_context("test")

        assert "Content 1" in result

    def test_handles_brace_extraction_fallback(self, tmp_library):
        """Router can extract JSON via first-{ to last-} (fallback 2)."""
        lib = Library(str(tmp_library))
        lib.add_skill("s1", "Skill 1", "Content 1")

        with patch("src.router.call_gemini") as mock_gemini:
            mock_gemini.return_value = 'Here is the result: {"skills": ["s1"], "tools": []} done'

            router = Router(lib)
            result = router.prepare_context("test")

        assert "Content 1" in result

    def test_nonexistent_selection_ignored(self, tmp_library):
        lib = Library(str(tmp_library))
        lib.add_skill("real-skill", "Real", "Real content")

        with patch("src.router.call_gemini") as mock_gemini:
            mock_gemini.return_value = json.dumps({"skills": ["real-skill", "fake-skill"], "tools": ["fake-tool"]})

            router = Router(lib)
            result = router.prepare_context("test")

        assert "Real content" in result
        # fake-skill and fake-tool silently skipped
