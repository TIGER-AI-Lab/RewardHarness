"""Dual Router for RewardHarness pipeline.

Uses Gemini API to select relevant Skills and Tools from the Library
based on the current editing prompt. Implements L1→L2 progressive disclosure.
"""

import json
import logging
import time

from src.gemini_client import call_gemini

logger = logging.getLogger(__name__)


ROUTING_PROMPT = '''You are selecting evaluation skills and visual analysis tools for an image editing quality evaluator.

Given the editing prompt below, select the skills and tools most relevant to evaluating this specific edit.
You decide how many to use — choose only what is genuinely useful. You may select zero if nothing applies.

Editing prompt: '{prompt}'

Available skills (evaluation guidance):
{skills_json}

Available tools (specialized VLM capabilities):
{tools_json}

Return JSON only: {{"skills": ["skill-name-1", ...], "tools": ["tool-name-1", ...]}}
Select only names that exist in the lists above.'''


class Router:
    def __init__(self, library, model: str = "gemini-3.1-pro-preview"):
        self.lib = library
        self.model = model

    def prepare_context(self, prompt: str) -> str:
        """Select relevant skills/tools and return assembled L2 context.

        Args:
            prompt: The editing instruction text

        Returns:
            Assembled context string to append to Sub-Agent system_prompt.
            Empty string if library is empty or nothing selected.
        """
        summaries = self.lib.get_all_summaries()

        # Empty library → no context (Iter 0 baseline)
        if not summaries["skills"] and not summaries["tools"]:
            return ""

        # Gemini selects relevant skills/tools
        routing_prompt = ROUTING_PROMPT.format(
            prompt=prompt,
            skills_json=json.dumps(summaries["skills"], indent=2),
            tools_json=json.dumps(summaries["tools"], indent=2)
        )

        selected = None
        for attempt in range(3):
            try:
                response_text = call_gemini(
                    user_message=routing_prompt,
                    model=self.model,
                    max_tokens=81920,
                    temperature=0,
                    response_mime_type="application/json",
                )

                selected = self._parse_response(response_text)
                if selected is not None:
                    break
                # Truncated response — retry after brief pause
                if attempt < 2:
                    logger.debug("Router retry %d/2 for truncated response", attempt + 1)
                    time.sleep(0.5)
            except Exception as e:
                if attempt < 2:
                    logger.debug("Router API error attempt %d: %s", attempt + 1, str(e)[:100])
                    time.sleep(1)
                    continue
                logger.warning("Router Gemini API unavailable, using all library entries: %s", str(e)[:100])
                selected = {
                    "skills": [s["name"] for s in summaries["skills"]],
                    "tools": [t["name"] for t in summaries["tools"]]
                }

        if selected is None:
            logger.warning("Router failed after 3 attempts, last response: %r", response_text[:300])
            selected = {"skills": [], "tools": []}

        logger.debug("Router selected skills=%s tools=%s (attempts=%d) for prompt='%s'",
                     selected.get("skills", []), selected.get("tools", []),
                     attempt + 1, prompt[:80])

        return self._assemble_context(selected)

    def _assemble_context(self, selected: dict) -> str:
        """Assemble L2 context string from selected skills/tools."""
        sections = []

        # Skills: full evaluation instruction documents
        skill_docs = []
        for name in selected.get("skills", []):
            try:
                content = self.lib.get_full_content(name)
                skill_docs.append(f"## Skill: {name}\n{content}")
            except KeyError:
                continue

        # Tools: body only (description + call format); system_prompt stays in frontmatter
        tool_docs = []
        for name in selected.get("tools", []):
            try:
                content = self.lib.get_full_content(name)
                tool_docs.append(f"## Tool: {name}\n{content}")
            except KeyError:
                continue

        if skill_docs:
            sections.append("# EVALUATION SKILLS\n" + "\n\n".join(skill_docs))
        if tool_docs:
            sections.append("# AVAILABLE TOOLS\n" + "\n\n".join(tool_docs))

        return "\n\n".join(sections)

    @staticmethod
    def _parse_response(response_text: str):
        """Parse JSON from Gemini response. Returns dict on success, None on failure."""
        try:
            return json.loads(response_text.strip())
        except (json.JSONDecodeError, IndexError):
            pass

        # Fallback 1: strip markdown fences
        json_text = response_text
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0]
        try:
            return json.loads(json_text.strip())
        except (json.JSONDecodeError, IndexError):
            pass

        # Fallback 2: extract first { to last }
        start = json_text.find("{")
        end = json_text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(json_text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None
