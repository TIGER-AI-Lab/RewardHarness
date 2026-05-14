"""Integration tests for ChainAnalyzer -> Evolver update chain.

Tests the full flow:
1. ChainAnalyzer.analyze() receives failure examples with reasoning chains
2. Claude API (mocked via OpenAI proxy pattern) returns fixed improvement_signals
3. Evolver.apply_signals() writes SKILL.md files via Library
4. Verify frontmatter + body content is correctly written
"""

import json
import os

import pytest
import yaml
from unittest.mock import MagicMock, patch

from src.chain_analyzer import ChainAnalyzer
from src.evolver import Evolver
from src.library import Library


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def failure_examples():
    """3 failure examples with reasoning chains."""
    return [
        {
            "group_id": "g001",
            "prompt": "Add a red hat to the person",
            "gt": "A",
            "prediction": "B",
            "correct": False,
            "reasoning_chain": (
                "Step 1: Examine source image - person without hat.\n"
                "Step 2: Image A adds a red hat, well-blended.\n"
                "Step 3: Image B adds a blue scarf instead.\n"
                "Conclusion: B follows instruction better.\n"
                "ERROR: Confused color fidelity with instruction adherence."
            ),
        },
        {
            "group_id": "g002",
            "prompt": "Remove the background clutter",
            "gt": "B",
            "prediction": "A",
            "correct": False,
            "reasoning_chain": (
                "Step 1: Source has cluttered background.\n"
                "Step 2: Image A partially removes clutter but introduces artifacts.\n"
                "Step 3: Image B cleanly removes clutter.\n"
                "Conclusion: A is cleaner.\n"
                "ERROR: Failed to detect artifacts in Image A."
            ),
        },
        {
            "group_id": "g003",
            "prompt": "Change the sky to sunset colors",
            "gt": "A",
            "prediction": "tie",
            "correct": False,
            "reasoning_chain": (
                "Step 1: Source shows daytime sky.\n"
                "Step 2: Image A has warm sunset tones.\n"
                "Step 3: Image B has slightly orange sky but unnatural.\n"
                "Conclusion: Both are acceptable, tie.\n"
                "ERROR: Should have scored instruction fidelity higher for A."
            ),
        },
    ]


@pytest.fixture
def fixed_signals():
    """Fixed improvement signals returned by mocked Claude API."""
    return {
        "skill_updates": [
            {
                "action": "add",
                "name": "instruction-fidelity-check",
                "description": "Verify edit matches the instruction precisely before comparing quality",
                "content_md": (
                    "## Instruction Fidelity Check\n\n"
                    "Before scoring quality, verify that the edit matches the "
                    "instruction:\n\n"
                    "1. Parse the instruction for the target object/action\n"
                    "2. Check if each image addresses the correct object\n"
                    "3. Penalize edits that modify the wrong attribute\n\n"
                    "### Common Failure Modes\n"
                    "- Confusing color changes with object additions\n"
                    "- Accepting partial compliance as full compliance"
                ),
            },
            {
                "action": "add",
                "name": "artifact-detection-rubric",
                "description": "Rubric for identifying visual artifacts in edited images",
                "content_md": (
                    "## Artifact Detection Rubric\n\n"
                    "Score artifact severity:\n"
                    "- 4: No artifacts\n"
                    "- 3: Minor artifacts (barely visible)\n"
                    "- 2: Noticeable artifacts (edges, blending)\n"
                    "- 1: Severe artifacts (distortion, ghosting)"
                ),
            },
        ],
        "tool_updates": [
            {
                "action": "add",
                "name": "edge-artifact-detector",
                "description": "Detect blending artifacts at edit boundaries",
                "system_prompt": (
                    "You are an artifact detection specialist. Examine the "
                    "boundary between edited and unedited regions. "
                    "Return JSON: {\"has_artifacts\": bool, \"severity\": 1-4, "
                    "\"locations\": [str]}"
                ),
                "input_schema": {"images": "list[base64_str]", "query": "str"},
                "output_schema": {
                    "has_artifacts": "bool",
                    "severity": "int",
                    "locations": "list[str]",
                },
                "content_md": (
                    "## Edge Artifact Detector\n\n"
                    "Specialized VLM tool for detecting visual artifacts."
                ),
            },
        ],
        "analysis_summary": (
            "Three failures identified: instruction fidelity confusion, "
            "artifact detection gaps, and overly lenient tie scoring."
        ),
    }


@pytest.fixture
def library_on_disk(tmp_path):
    """Create a Library backed by a real temporary directory."""
    lib_dir = tmp_path / "library"
    lib_dir.mkdir()
    (lib_dir / "skills").mkdir()
    (lib_dir / "tools").mkdir()
    (lib_dir / "registry.json").write_text("{}")
    return Library(str(lib_dir))


# ---------------------------------------------------------------------------
# ChainAnalyzer unit tests
# ---------------------------------------------------------------------------

class TestChainAnalyzerFormat:
    """Verify _format_example produces expected text."""

    def test_format_correct(self):
        analyzer = ChainAnalyzer.__new__(ChainAnalyzer)
        ex = {
            "group_id": "g1", "prompt": "test", "gt": "A",
            "prediction": "A", "correct": True,
            "reasoning_chain": "chain text",
        }
        text = analyzer._format_example(ex)
        assert "CORRECT" in text
        assert "g1" in text
        assert "chain text" in text

    def test_format_incorrect(self):
        analyzer = ChainAnalyzer.__new__(ChainAnalyzer)
        ex = {
            "group_id": "g2", "prompt": "edit", "gt": "B",
            "prediction": "A", "correct": False,
            "reasoning_chain": "wrong chain",
        }
        text = analyzer._format_example(ex)
        assert "INCORRECT" in text

    def test_format_missing_keys(self):
        """Missing keys default to N/A."""
        analyzer = ChainAnalyzer.__new__(ChainAnalyzer)
        text = analyzer._format_example({})
        assert "N/A" in text


class TestChainAnalyzerValidation:
    """Test _validate_skill_updates and _validate_tool_updates."""

    def _make_analyzer(self):
        return ChainAnalyzer.__new__(ChainAnalyzer)

    # ---- skill_updates ----

    def test_valid_skill_add(self):
        a = self._make_analyzer()
        updates = [{"action": "add", "name": "s1",
                     "description": "desc", "content_md": "body"}]
        result = a._validate_skill_updates(updates)
        assert len(result) == 1

    def test_skill_add_missing_description(self):
        a = self._make_analyzer()
        updates = [{"action": "add", "name": "s1", "content_md": "body"}]
        result = a._validate_skill_updates(updates)
        assert len(result) == 0

    def test_skill_add_missing_content_md(self):
        a = self._make_analyzer()
        updates = [{"action": "add", "name": "s1", "description": "d"}]
        result = a._validate_skill_updates(updates)
        assert len(result) == 0

    def test_skill_update_missing_content_md(self):
        a = self._make_analyzer()
        updates = [{"action": "update", "name": "s1"}]
        result = a._validate_skill_updates(updates)
        assert len(result) == 0

    def test_skill_update_valid(self):
        a = self._make_analyzer()
        updates = [{"action": "update", "name": "s1", "content_md": "new"}]
        result = a._validate_skill_updates(updates)
        assert len(result) == 1

    def test_skill_delete_action(self):
        a = self._make_analyzer()
        updates = [{"action": "delete", "name": "s1"}]
        result = a._validate_skill_updates(updates)
        assert len(result) == 1  # delete is valid, only requires name

    def test_skill_unknown_action(self):
        a = self._make_analyzer()
        updates = [{"action": "foobar", "name": "s1"}]
        result = a._validate_skill_updates(updates)
        assert len(result) == 0

    def test_skill_missing_name(self):
        a = self._make_analyzer()
        updates = [{"action": "add", "description": "d", "content_md": "b"}]
        result = a._validate_skill_updates(updates)
        assert len(result) == 0

    # ---- tool_updates ----

    def test_valid_tool_add(self):
        a = self._make_analyzer()
        updates = [{"action": "add", "name": "t1",
                     "description": "desc", "system_prompt": "sp"}]
        result = a._validate_tool_updates(updates)
        assert len(result) == 1

    def test_tool_add_missing_system_prompt(self):
        a = self._make_analyzer()
        updates = [{"action": "add", "name": "t1", "description": "desc"}]
        result = a._validate_tool_updates(updates)
        assert len(result) == 0

    def test_tool_add_missing_description(self):
        a = self._make_analyzer()
        updates = [{"action": "add", "name": "t1", "system_prompt": "sp"}]
        result = a._validate_tool_updates(updates)
        assert len(result) == 0

    def test_tool_update_missing_system_prompt(self):
        a = self._make_analyzer()
        updates = [{"action": "update", "name": "t1"}]
        result = a._validate_tool_updates(updates)
        assert len(result) == 0

    def test_tool_update_valid(self):
        a = self._make_analyzer()
        updates = [{"action": "update", "name": "t1", "system_prompt": "new"}]
        result = a._validate_tool_updates(updates)
        assert len(result) == 1

    def test_tool_delete_action(self):
        a = self._make_analyzer()
        updates = [{"action": "delete", "name": "t1"}]
        result = a._validate_tool_updates(updates)
        assert len(result) == 1

    def test_tool_unknown_action(self):
        a = self._make_analyzer()
        updates = [{"action": "foobar", "name": "t1"}]
        result = a._validate_tool_updates(updates)
        assert len(result) == 0

    def test_mixed_valid_invalid(self):
        """Only valid entries survive validation."""
        a = self._make_analyzer()
        updates = [
            {"action": "add", "name": "ok", "description": "d", "system_prompt": "sp"},
            {"action": "add", "name": "bad"},  # missing fields
            {"action": "update", "name": "ok2", "system_prompt": "sp2"},
        ]
        result = a._validate_tool_updates(updates)
        assert len(result) == 2
        assert result[0]["name"] == "ok"
        assert result[1]["name"] == "ok2"


# ---------------------------------------------------------------------------
# ChainAnalyzer.analyze() with mocked Claude API
# ---------------------------------------------------------------------------

class TestChainAnalyzerAnalyze:

    @patch("src.chain_analyzer.call_gemini")
    def test_analyze_returns_signals(self, mock_gemini, failure_examples, fixed_signals):
        """ChainAnalyzer.analyze() calls Gemini and returns parsed signals."""
        mock_gemini.return_value = json.dumps(fixed_signals)

        analyzer = ChainAnalyzer(model="gemini-3.1-pro-preview")

        current_library = {"skills": [], "tools": []}
        signals = analyzer.analyze(failure_examples, current_library)

        # Verify Gemini was called once
        mock_gemini.assert_called_once()
        call_kwargs = mock_gemini.call_args
        assert call_kwargs.kwargs["model"] == "gemini-3.1-pro-preview"

        # Verify prompt contains all 3 examples
        prompt_text = call_kwargs.kwargs["user_message"]
        assert "g001" in prompt_text
        assert "g002" in prompt_text
        assert "g003" in prompt_text
        assert "INCORRECT" in prompt_text

        # Verify returned signals structure
        assert len(signals["skill_updates"]) == 2
        assert len(signals["tool_updates"]) == 1
        assert "analysis_summary" in signals
        assert signals["skill_updates"][0]["name"] == "instruction-fidelity-check"
        assert signals["tool_updates"][0]["name"] == "edge-artifact-detector"

    @patch("src.chain_analyzer.call_gemini")
    def test_analyze_json_in_fenced_block(self, mock_gemini, failure_examples, fixed_signals):
        """ChainAnalyzer handles JSON wrapped in ```json ... ``` fences."""
        mock_gemini.return_value = (
            "Here is my analysis:\n\n```json\n"
            + json.dumps(fixed_signals)
            + "\n```\n\nHope this helps."
        )

        analyzer = ChainAnalyzer()
        signals = analyzer.analyze(failure_examples, {"skills": [], "tools": []})

        assert len(signals["skill_updates"]) == 2
        assert signals["skill_updates"][1]["name"] == "artifact-detection-rubric"

    @patch("src.chain_analyzer.call_gemini")
    def test_analyze_invalid_json_fallback(self, mock_gemini, failure_examples):
        """ChainAnalyzer returns empty signals on unparseable response."""
        mock_gemini.return_value = "This is not JSON at all {{{broken"

        analyzer = ChainAnalyzer()
        signals = analyzer.analyze(failure_examples, {"skills": [], "tools": []})

        assert signals["skill_updates"] == []
        assert signals["tool_updates"] == []
        assert "Failed to parse" in signals["analysis_summary"]

    @patch("src.chain_analyzer.call_gemini")
    def test_analyze_validation_filters_malformed(self, mock_gemini, failure_examples):
        """Malformed entries inside skill_updates/tool_updates are filtered out."""
        bad_signals = {
            "skill_updates": [
                # Valid
                {"action": "add", "name": "good-skill",
                 "description": "ok", "content_md": "## Good"},
                # Invalid: missing content_md
                {"action": "add", "name": "bad-skill",
                 "description": "ok"},
            ],
            "tool_updates": [
                # Invalid: missing system_prompt
                {"action": "add", "name": "bad-tool", "description": "ok"},
            ],
            "analysis_summary": "test",
        }
        mock_gemini.return_value = json.dumps(bad_signals)

        analyzer = ChainAnalyzer()
        signals = analyzer.analyze(failure_examples, {"skills": [], "tools": []})

        assert len(signals["skill_updates"]) == 1
        assert signals["skill_updates"][0]["name"] == "good-skill"
        assert len(signals["tool_updates"]) == 0


# ---------------------------------------------------------------------------
# Evolver.apply_signals() -> Library -> SKILL.md on disk
# ---------------------------------------------------------------------------

class TestEvolverApplySignals:

    def test_add_skills_writes_skill_md(self, library_on_disk, fixed_signals):
        """Evolver writes SKILL.md files with correct frontmatter and body."""
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        applied = evolver.apply_signals(fixed_signals)

        assert applied["skills_added"] == 2
        assert applied["tools_added"] == 1

        # ---- Check skill: instruction-fidelity-check ----
        skill_path = os.path.join(
            library_on_disk.base_dir, "skills",
            "instruction-fidelity-check", "SKILL.md"
        )
        assert os.path.exists(skill_path), f"SKILL.md not written at {skill_path}"

        parsed = library_on_disk._parse_skill_md(skill_path)
        fm = parsed["frontmatter"]
        body = parsed["body"]

        assert fm["name"] == "instruction-fidelity-check"
        assert fm["type"] == "skill"
        assert "instruction" in fm["description"].lower()
        assert "## Instruction Fidelity Check" in body
        assert "Common Failure Modes" in body

        # ---- Check skill: artifact-detection-rubric ----
        skill2_path = os.path.join(
            library_on_disk.base_dir, "skills",
            "artifact-detection-rubric", "SKILL.md"
        )
        assert os.path.exists(skill2_path)
        parsed2 = library_on_disk._parse_skill_md(skill2_path)
        assert parsed2["frontmatter"]["name"] == "artifact-detection-rubric"
        assert "Score artifact severity" in parsed2["body"]

        # ---- Check tool: edge-artifact-detector ----
        tool_path = os.path.join(
            library_on_disk.base_dir, "tools",
            "edge-artifact-detector", "SKILL.md"
        )
        assert os.path.exists(tool_path)
        tool_parsed = library_on_disk._parse_skill_md(tool_path)
        tfm = tool_parsed["frontmatter"]
        assert tfm["name"] == "edge-artifact-detector"
        assert tfm["type"] == "tool"
        assert "artifact detection specialist" in tfm["system_prompt"]
        assert tfm["input_schema"] == {"images": "list[base64_str]", "query": "str"}

    def test_registry_updated(self, library_on_disk, fixed_signals):
        """After apply_signals, registry.json reflects added entries."""
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        evolver.apply_signals(fixed_signals)

        # Re-read from disk
        library_on_disk.load_registry()
        reg = library_on_disk.registry

        assert "instruction-fidelity-check" in reg
        assert reg["instruction-fidelity-check"]["type"] == "skill"
        assert "artifact-detection-rubric" in reg
        assert "edge-artifact-detector" in reg
        assert reg["edge-artifact-detector"]["type"] == "tool"

    def test_update_existing_skill(self, library_on_disk):
        """Evolver handles 'update' action for existing skills."""
        # First add a skill
        library_on_disk.add_skill(
            "old-skill", "Old description", "## Old Content"
        )

        signals = {
            "skill_updates": [
                {
                    "action": "update",
                    "name": "old-skill",
                    "description": "Updated description",
                    "content_md": "## Updated Content\n\nNew rubric here.",
                },
            ],
            "tool_updates": [],
            "analysis_summary": "Updated old-skill",
        }

        evolver = Evolver(library_on_disk, endpoint_pool=None)
        applied = evolver.apply_signals(signals)

        assert applied["skills_updated"] == 1

        # Verify file updated
        skill = library_on_disk.get_skill("old-skill")
        assert "Updated Content" in skill["content"]
        assert skill["description"] == "Updated description"

    def test_update_nonexistent_skill_logged_not_crash(self, library_on_disk):
        """Updating a non-existent skill logs error but doesn't crash."""
        signals = {
            "skill_updates": [
                {"action": "update", "name": "ghost-skill", "content_md": "body"},
            ],
            "tool_updates": [],
            "analysis_summary": "test",
        }
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        applied = evolver.apply_signals(signals)

        # Should have caught the KeyError and logged it
        assert applied["skills_updated"] == 0

    def test_empty_signals(self, library_on_disk):
        """Empty signals produce zero changes."""
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        applied = evolver.apply_signals({
            "skill_updates": [],
            "tool_updates": [],
            "analysis_summary": "nothing to do",
        })
        assert applied == {
            "skills_added": 0, "skills_updated": 0, "skills_deleted": 0,
            "tools_added": 0, "tools_updated": 0, "tools_deleted": 0,
        }

    def test_signals_with_missing_keys_safe(self, library_on_disk):
        """Evolver.apply_signals uses .get() and handles missing keys."""
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        # Completely empty dict
        applied = evolver.apply_signals({})
        assert applied["skills_added"] == 0
        assert applied["tools_added"] == 0

    def test_delete_skill(self, library_on_disk):
        """Evolver handles skill delete action."""
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        # First add a skill
        library_on_disk.add_skill("to-delete", "temp", "temp content")
        assert "to-delete" in library_on_disk.registry

        # Delete via signals
        applied = evolver.apply_signals({
            "skill_updates": [{"action": "delete", "name": "to-delete", "reason": "redundant"}],
            "tool_updates": [],
        })
        assert applied["skills_deleted"] == 1
        assert "to-delete" not in library_on_disk.registry

    def test_delete_tool(self, library_on_disk):
        """Evolver handles tool delete action."""
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        # First add a tool
        library_on_disk.add_tool("tool-del", "temp", "sp", {}, {}, "md")
        assert "tool-del" in library_on_disk.registry

        # Delete via signals
        applied = evolver.apply_signals({
            "skill_updates": [],
            "tool_updates": [{"action": "delete", "name": "tool-del", "reason": "harmful"}],
        })
        assert applied["tools_deleted"] == 1
        assert "tool-del" not in library_on_disk.registry

    def test_delete_nonexistent_skill_logs_error(self, library_on_disk):
        """Deleting a nonexistent skill logs error but doesn't crash."""
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        applied = evolver.apply_signals({
            "skill_updates": [{"action": "delete", "name": "nonexistent"}],
            "tool_updates": [],
        })
        assert applied["skills_deleted"] == 0


# ---------------------------------------------------------------------------
# End-to-end integration: ChainAnalyzer -> Evolver -> Disk
# ---------------------------------------------------------------------------

class TestChainEvolverIntegration:

    @patch("src.chain_analyzer.call_gemini")
    def test_full_chain_analyzer_to_evolver(
        self, mock_gemini, failure_examples, fixed_signals, library_on_disk
    ):
        """Full integration: analyze failures -> produce signals -> evolve library -> verify disk."""
        # 1. Mock Gemini API to return fixed_signals
        mock_gemini.return_value = json.dumps(fixed_signals)

        # 2. ChainAnalyzer.analyze()
        analyzer = ChainAnalyzer(model="gemini-3.1-pro-preview")
        current_lib = library_on_disk.get_all_summaries()
        signals = analyzer.analyze(failure_examples, current_lib)

        # 3. Evolver.apply_signals()
        evolver = Evolver(library_on_disk, endpoint_pool=None)
        applied = evolver.apply_signals(signals)

        # 4. Verify results
        assert applied["skills_added"] == 2
        assert applied["tools_added"] == 1

        # Verify SKILL.md files on disk
        for skill_name in ["instruction-fidelity-check", "artifact-detection-rubric"]:
            path = os.path.join(
                library_on_disk.base_dir, "skills", skill_name, "SKILL.md"
            )
            assert os.path.exists(path), f"Missing: {path}"

            with open(path) as f:
                raw = f.read()
            # Must start with frontmatter delimiter
            assert raw.startswith("---\n")
            # Must have closing delimiter
            assert "\n---\n" in raw

            parsed = library_on_disk._parse_skill_md(path)
            assert parsed["frontmatter"]["name"] == skill_name
            assert parsed["frontmatter"]["type"] == "skill"
            assert len(parsed["body"]) > 0

        # Verify tool SKILL.md
        tool_path = os.path.join(
            library_on_disk.base_dir, "tools",
            "edge-artifact-detector", "SKILL.md"
        )
        assert os.path.exists(tool_path)
        tool_parsed = library_on_disk._parse_skill_md(tool_path)
        assert tool_parsed["frontmatter"]["type"] == "tool"
        assert "system_prompt" in tool_parsed["frontmatter"]

        # Verify registry persistence
        reg_path = os.path.join(library_on_disk.base_dir, "registry.json")
        with open(reg_path) as f:
            disk_reg = json.load(f)
        assert len(disk_reg) == 3
        assert "instruction-fidelity-check" in disk_reg
        assert "edge-artifact-detector" in disk_reg

    @patch("src.chain_analyzer.call_gemini")
    def test_snapshot_restore_after_evolution(
        self, mock_gemini, failure_examples, fixed_signals, library_on_disk
    ):
        """After evolving, snapshot/restore correctly rolls back."""
        mock_gemini.return_value = json.dumps(fixed_signals)

        evolver = Evolver(library_on_disk, endpoint_pool=None)

        # Snapshot empty state
        snap_empty = evolver.snapshot()
        assert len(snap_empty["registry"]) == 0

        # Evolve
        analyzer = ChainAnalyzer()
        signals = analyzer.analyze(failure_examples, library_on_disk.get_all_summaries())
        evolver.apply_signals(signals)

        # Verify evolution happened
        assert len(library_on_disk.registry) == 3

        # Snapshot evolved state
        snap_evolved = evolver.snapshot()
        assert len(snap_evolved["registry"]) == 3

        # Restore to empty
        evolver.restore(snap_empty)
        assert len(library_on_disk.registry) == 0

        # Verify files cleaned up
        skill_path = os.path.join(
            library_on_disk.base_dir, "skills",
            "instruction-fidelity-check", "SKILL.md"
        )
        assert not os.path.exists(skill_path)

        # Restore evolved state
        evolver.restore(snap_evolved)
        assert len(library_on_disk.registry) == 3
        assert "instruction-fidelity-check" in library_on_disk.registry
