"""Integration test for Library: full lifecycle from empty library through
snapshot/restore and registry persistence.

Run with:  cd /path/to/your/reward-harness-checkout && python -m pytest tests/test_library_integration.py -v
"""

import json
import os

import pytest
import yaml

from src.library import Library


class TestLibraryFullLifecycle:
    """Walk through every lifecycle step on a single temp library."""

    # -- fixtures --------------------------------------------------------

    @pytest.fixture(autouse=True)
    def setup_library(self, tmp_path):
        """Create a fresh library directory for each test method."""
        self.lib_dir = tmp_path / "library"
        self.lib_dir.mkdir()
        (self.lib_dir / "skills").mkdir()
        (self.lib_dir / "tools").mkdir()
        self.lib = Library(str(self.lib_dir))

    # -- helpers ---------------------------------------------------------

    def _read_skill_md(self, rel_path: str) -> str:
        """Read raw SKILL.md content from the library directory."""
        path = self.lib_dir / rel_path
        return path.read_text()

    def _parse_frontmatter(self, raw: str) -> dict:
        """Extract YAML frontmatter dict from raw SKILL.md text."""
        lines = raw.split("\n")
        assert lines[0].strip() == "---", "SKILL.md must start with ---"
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        assert end is not None, "No closing --- found"
        return yaml.safe_load("\n".join(lines[1:end]))

    def _parse_body(self, raw: str) -> str:
        """Extract body (everything after second ---) from raw SKILL.md text."""
        lines = raw.split("\n")
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        assert end is not None
        return "\n".join(lines[end + 1 :]).strip()

    # ================================================================== #
    #  Step 1: Empty library                                              #
    # ================================================================== #

    def test_01_empty_library(self):
        summaries = self.lib.get_all_summaries()
        assert summaries == {"skills": [], "tools": []}, (
            "Fresh library must return empty skill/tool lists"
        )

    # ================================================================== #
    #  Step 2: add_skill -> verify SKILL.md created                       #
    # ================================================================== #

    def test_02_add_skill_creates_skill_md(self):
        self.lib.add_skill(
            "color-check",
            "Check color consistency",
            "## Color Check\nVerify colors match the surrounding context.",
        )

        # File must exist
        skill_path = self.lib_dir / "skills" / "color-check" / "SKILL.md"
        assert skill_path.exists(), "SKILL.md file not created"

        # Frontmatter check
        raw = skill_path.read_text()
        fm = self._parse_frontmatter(raw)
        assert fm["name"] == "color-check"
        assert fm["type"] == "skill"
        assert fm["description"] == "Check color consistency"

        # Body check
        body = self._parse_body(raw)
        assert "## Color Check" in body
        assert "Verify colors match" in body

    # ================================================================== #
    #  Step 3: get_skill -> returns correct content                       #
    # ================================================================== #

    def test_03_get_skill_returns_correct_content(self):
        self.lib.add_skill("edge-detect", "Edge sharpness", "## Edges\nMust be crisp.")

        result = self.lib.get_skill("edge-detect")
        assert result["name"] == "edge-detect"
        assert result["description"] == "Edge sharpness"
        assert "## Edges" in result["content"]
        assert "Must be crisp" in result["content"]

    # ================================================================== #
    #  Step 4: update_skill -> body changes, frontmatter preserved        #
    # ================================================================== #

    def test_04_update_skill_body_changes_frontmatter_preserved(self):
        self.lib.add_skill("edge-detect", "Edge sharpness", "## Old Body")

        # Update without new_description -> description preserved
        self.lib.update_skill("edge-detect", "## New Body\nImproved criteria.")

        result = self.lib.get_skill("edge-detect")
        assert result["description"] == "Edge sharpness", (
            "Description must be preserved when new_description not given"
        )
        assert "## New Body" in result["content"]
        assert "Old Body" not in result["content"]

        # Verify frontmatter on disk still has original metadata
        raw = self._read_skill_md("skills/edge-detect/SKILL.md")
        fm = self._parse_frontmatter(raw)
        assert fm["name"] == "edge-detect"
        assert fm["type"] == "skill"
        assert fm["description"] == "Edge sharpness"

    def test_04b_update_skill_with_new_description(self):
        self.lib.add_skill("edge-detect", "Edge sharpness", "## Old Body")
        self.lib.update_skill(
            "edge-detect", "## Updated Body", new_description="Better edge check"
        )

        result = self.lib.get_skill("edge-detect")
        assert result["description"] == "Better edge check"
        assert "## Updated Body" in result["content"]

    # ================================================================== #
    #  Step 5: add_tool -> SKILL.md with system_prompt in frontmatter     #
    # ================================================================== #

    def test_05_add_tool_creates_skill_md_with_system_prompt(self):
        self.lib.add_tool(
            name="tool-ocr",
            description="Extract text from images",
            system_prompt="You are an OCR tool. Return JSON.",
            input_schema={"images": "list[base64_str]", "query": "str"},
            output_schema={"text": "str", "confidence": "float"},
            content_md="## Tool: OCR\nExtracts text from images.",
        )

        tool_path = self.lib_dir / "tools" / "tool-ocr" / "SKILL.md"
        assert tool_path.exists(), "Tool SKILL.md not created"

        raw = tool_path.read_text()
        fm = self._parse_frontmatter(raw)
        assert fm["name"] == "tool-ocr"
        assert fm["type"] == "tool"
        assert fm["description"] == "Extract text from images"
        assert fm["system_prompt"] == "You are an OCR tool. Return JSON."
        assert fm["input_schema"] == {"images": "list[base64_str]", "query": "str"}
        assert fm["output_schema"] == {"text": "str", "confidence": "float"}

        body = self._parse_body(raw)
        assert "## Tool: OCR" in body

    # ================================================================== #
    #  Step 6: update_tool -> only system_prompt changes                  #
    # ================================================================== #

    def test_06_update_tool_only_changes_system_prompt(self):
        self.lib.add_tool(
            "tool-ocr", "Extract text", "Original OCR prompt",
            {"images": "list"}, {"text": "str"},
            "## OCR Tool\nOriginal body content.",
        )

        self.lib.update_tool("tool-ocr", "Updated OCR prompt v2")

        # system_prompt must change
        tool = self.lib.get_tool("tool-ocr")
        assert tool["system_prompt"] == "Updated OCR prompt v2"

        # body must remain unchanged
        body_content = self.lib.get_full_content("tool-ocr")
        assert "## OCR Tool" in body_content
        assert "Original body content" in body_content

        # Other frontmatter fields must be unchanged
        raw = self._read_skill_md("tools/tool-ocr/SKILL.md")
        fm = self._parse_frontmatter(raw)
        assert fm["description"] == "Extract text"
        assert fm["input_schema"] == {"images": "list"}
        assert fm["output_schema"] == {"text": "str"}

    # ================================================================== #
    #  Step 7: get_tool -> returns correct system_prompt                  #
    # ================================================================== #

    def test_07_get_tool_returns_correct_system_prompt(self):
        self.lib.add_tool(
            "tool-seg", "Segment regions", "You are a segmentation tool.",
            {"images": "list"}, {"regions": "list"},
            "## Segmentation\nIdentify regions.",
        )

        tool = self.lib.get_tool("tool-seg")
        assert tool["name"] == "tool-seg"
        assert tool["description"] == "Segment regions"
        assert tool["system_prompt"] == "You are a segmentation tool."
        assert tool["input_schema"] == {"images": "list"}
        assert tool["output_schema"] == {"regions": "list"}

    # ================================================================== #
    #  Step 8: Snapshot -> verify all content captured                     #
    # ================================================================== #

    def test_08_snapshot_captures_all(self):
        self.lib.add_skill("s1", "Skill one", "## S1 Body")
        self.lib.add_tool(
            "t1", "Tool one", "sys prompt 1", {"in": "x"}, {"out": "y"}, "## T1 Body"
        )

        snap = self.lib.snapshot()

        # Registry captured
        assert "s1" in snap["registry"]
        assert "t1" in snap["registry"]
        assert snap["registry"]["s1"]["type"] == "skill"
        assert snap["registry"]["t1"]["type"] == "tool"

        # Files captured
        assert "skills/s1/SKILL.md" in snap["files"]
        assert "tools/t1/SKILL.md" in snap["files"]
        assert "## S1 Body" in snap["files"]["skills/s1/SKILL.md"]
        assert "## T1 Body" in snap["files"]["tools/t1/SKILL.md"]

    # ================================================================== #
    #  Steps 9-10: Add after snapshot, then restore                       #
    # ================================================================== #

    def test_09_10_add_after_snapshot_then_restore(self):
        # Setup: add initial items
        self.lib.add_skill("s1", "Skill one", "## S1 Body")
        self.lib.add_tool(
            "t1", "Tool one", "sys prompt 1", {"in": "x"}, {"out": "y"}, "## T1 Body"
        )

        # Take snapshot
        snap = self.lib.snapshot()

        # Step 9: Add more items after snapshot
        self.lib.add_skill("s2", "Skill two", "## S2 Body")
        self.lib.add_tool(
            "t2", "Tool two", "sys prompt 2", {}, {}, "## T2 Body"
        )
        # Also modify an existing item
        self.lib.update_skill("s1", "## S1 Modified Body")

        # Verify post-snapshot additions exist
        assert "s2" in self.lib.registry
        assert "t2" in self.lib.registry
        assert (self.lib_dir / "skills" / "s2" / "SKILL.md").exists()
        assert (self.lib_dir / "tools" / "t2" / "SKILL.md").exists()

        # Step 10: Restore -> state must match snapshot exactly
        self.lib.restore(snap)

        # New items must be gone from registry
        assert "s2" not in self.lib.registry
        assert "t2" not in self.lib.registry

        # New item files must be removed
        assert not (self.lib_dir / "skills" / "s2" / "SKILL.md").exists()
        assert not (self.lib_dir / "tools" / "t2" / "SKILL.md").exists()

        # Original items must exist with snapshot-time content
        assert "s1" in self.lib.registry
        assert "t1" in self.lib.registry
        s1 = self.lib.get_skill("s1")
        assert "## S1 Body" in s1["content"], (
            "Restored skill must have original body, not modified"
        )
        assert "Modified" not in s1["content"]

        t1 = self.lib.get_tool("t1")
        assert t1["system_prompt"] == "sys prompt 1"

        # Summaries must match snapshot
        summaries = self.lib.get_all_summaries()
        skill_names = {s["name"] for s in summaries["skills"]}
        tool_names = {t["name"] for t in summaries["tools"]}
        assert skill_names == {"s1"}
        assert tool_names == {"t1"}

    # ================================================================== #
    #  Step 11: Registry persistence                                      #
    # ================================================================== #

    def test_11_registry_persistence(self):
        self.lib.add_skill("persistent-skill", "Persists across loads", "## Persist")
        self.lib.add_tool(
            "persistent-tool", "Also persists", "persist prompt",
            {"in": "a"}, {"out": "b"}, "## Persist Tool"
        )

        # Create a completely new Library instance from the same directory
        lib2 = Library(str(self.lib_dir))

        # Registry must contain both entries
        assert "persistent-skill" in lib2.registry
        assert "persistent-tool" in lib2.registry

        # Data must be readable
        skill = lib2.get_skill("persistent-skill")
        assert skill["description"] == "Persists across loads"
        assert "## Persist" in skill["content"]

        tool = lib2.get_tool("persistent-tool")
        assert tool["system_prompt"] == "persist prompt"

        # Summaries must match
        summaries = lib2.get_all_summaries()
        assert len(summaries["skills"]) == 1
        assert len(summaries["tools"]) == 1

    # ================================================================== #
    #  Full end-to-end lifecycle in one test                              #
    # ================================================================== #

    def test_full_lifecycle_end_to_end(self):
        """Walk through every step sequentially in one test to validate
        the full lifecycle from empty library through snapshot/restore."""

        # 1. Empty
        assert self.lib.get_all_summaries() == {"skills": [], "tools": []}

        # 2. add_skill
        self.lib.add_skill("eval-color", "Color eval", "## Color\nCheck hues.")
        raw = self._read_skill_md("skills/eval-color/SKILL.md")
        fm = self._parse_frontmatter(raw)
        assert fm["name"] == "eval-color"
        assert fm["type"] == "skill"
        body = self._parse_body(raw)
        assert "Check hues" in body

        # 3. get_skill
        skill = self.lib.get_skill("eval-color")
        assert skill["name"] == "eval-color"
        assert skill["description"] == "Color eval"
        assert "Check hues" in skill["content"]

        # 4. update_skill (body changes, frontmatter preserved)
        self.lib.update_skill("eval-color", "## Color v2\nImproved hue check.")
        skill = self.lib.get_skill("eval-color")
        assert skill["description"] == "Color eval"  # preserved
        assert "Improved hue check" in skill["content"]
        assert "Check hues" not in skill["content"]

        # 5. add_tool
        self.lib.add_tool(
            "vlm-ocr", "OCR tool", "You read text.",
            {"images": "list"}, {"text": "str"},
            "## OCR\nRead text from images.",
        )
        raw_tool = self._read_skill_md("tools/vlm-ocr/SKILL.md")
        fm_tool = self._parse_frontmatter(raw_tool)
        assert fm_tool["system_prompt"] == "You read text."

        # 6. update_tool (only system_prompt changes)
        self.lib.update_tool("vlm-ocr", "You read text v2.")
        tool = self.lib.get_tool("vlm-ocr")
        assert tool["system_prompt"] == "You read text v2."
        body_tool = self.lib.get_full_content("vlm-ocr")
        assert "Read text from images" in body_tool  # body unchanged

        # 7. get_tool
        tool = self.lib.get_tool("vlm-ocr")
        assert tool["name"] == "vlm-ocr"
        assert tool["system_prompt"] == "You read text v2."

        # 8. Snapshot
        snap = self.lib.snapshot()
        assert "eval-color" in snap["registry"]
        assert "vlm-ocr" in snap["registry"]
        assert len(snap["files"]) == 2

        # 9. Add more items after snapshot
        self.lib.add_skill("extra-skill", "Extra", "## Extra")
        self.lib.add_tool("extra-tool", "Extra t", "extra prompt", {}, {}, "## E")
        assert len(self.lib.get_all_summaries()["skills"]) == 2
        assert len(self.lib.get_all_summaries()["tools"]) == 2

        # 10. Restore
        self.lib.restore(snap)
        assert "extra-skill" not in self.lib.registry
        assert "extra-tool" not in self.lib.registry
        summaries = self.lib.get_all_summaries()
        assert len(summaries["skills"]) == 1
        assert len(summaries["tools"]) == 1
        assert summaries["skills"][0]["name"] == "eval-color"
        assert summaries["tools"][0]["name"] == "vlm-ocr"
        # Restored content must match snapshot time
        assert "Improved hue check" in self.lib.get_skill("eval-color")["content"]
        assert self.lib.get_tool("vlm-ocr")["system_prompt"] == "You read text v2."

        # 11. Registry persistence
        lib2 = Library(str(self.lib_dir))
        assert "eval-color" in lib2.registry
        assert "vlm-ocr" in lib2.registry
        assert "extra-skill" not in lib2.registry
        assert "extra-tool" not in lib2.registry
        assert lib2.get_skill("eval-color")["description"] == "Color eval"
