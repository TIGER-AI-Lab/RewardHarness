"""Chain Analyzer for RewardHarness pipeline.

Uses Gemini API to analyze reasoning chains from Sub-Agent predictions,
producing improvement signals for Skills and Tools evolution.
"""

import json
import logging
import re
import time

from src.gemini_client import call_gemini

logger = logging.getLogger(__name__)


ANALYSIS_PROMPT = '''You are analyzing reasoning chains from an image editing quality evaluator (Sub-Agent).
Your goal: identify patterns in correct AND incorrect predictions to improve the Sub-Agent's accuracy.

## Current Library State
Skills: {skills_summary}
Tools: {tools_summary}

## Evaluation Results
The following are ALL results from this iteration (both correct and incorrect):

{examples_text}

## Your Task
Analyze ALL results (correct and incorrect) to produce improvement signals:

1. **From CORRECT predictions**: Extract effective reasoning patterns, judgment heuristics, or visual analysis strategies worth codifying as reusable Skills. If a correct chain shows a particularly good approach, it should be captured.

2. **From INCORRECT predictions**: Identify gaps, systematic biases, or missing capabilities. Determine whether a new Skill (evaluation guidance) or Tool (specialized VLM capability) would help.

3. **For existing Skills/Tools**: Check if any need updates (unclear rubrics, misleading descriptions, suboptimal system_prompts).

## Output Format
Return ONLY valid JSON:
{{
  "skill_updates": [
    {{
      "action": "add",
      "name": "<kebab-case-name>",
      "description": "<one-line L1 summary for routing>",
      "content_md": "<full Markdown body: evaluation instructions, rubric, reasoning guides, etc.>"
    }},
    {{
      "action": "update",
      "name": "<existing-skill-name>",
      "description": "<updated L1 summary or null to keep existing>",
      "content_md": "<updated Markdown body>"
    }},
    {{
      "action": "delete",
      "name": "<existing-skill-name>",
      "reason": "<why this skill should be removed>"
    }}
  ],
  "tool_updates": [
    {{
      "action": "add",
      "name": "<tool-kebab-name>",
      "description": "<one-line L1 summary>",
      "system_prompt": "<VLM system prompt for specialized analysis>",
      "input_schema": {{"images": "list[base64_str]", "query": "str"}},
      "output_schema": {{"<key>": "<type>"}},
      "content_md": "<Markdown body: tool description + call format example>"
    }},
    {{
      "action": "update",
      "name": "<existing-tool-name>",
      "system_prompt": "<updated VLM system prompt>"
    }},
    {{
      "action": "delete",
      "name": "<existing-tool-name>",
      "reason": "<why this tool should be removed>"
    }}
  ],
  "analysis_summary": "<brief summary of what was found and why these changes help>"
}}

Rules:
- Skills can be ANY form of knowledge useful to the Sub-Agent (evaluation rubrics, reasoning patterns, failure mode checklists, domain heuristics, etc.)
- Tools are specialized VLM capabilities called via API (OCR, detection, color analysis, etc.) — each needs a system_prompt
- For "add": provide ALL required fields
- For "update": provide only the fields being changed (name is always required)
- Be specific and actionable in content_md — vague guidance won't help the Sub-Agent
- Consider the current library state to avoid duplicates
- For "delete": provide name and reason; use this to remove harmful, redundant, or contradictory skills/tools
- Return empty lists if no improvements are needed (rare)

CRITICAL CONSTRAINTS — Position Invariance:
- Skills MUST be position-invariant: NEVER refer to "Image A" or "Image B" by position
- Use "the image that [condition]" instead of positional references
- If existing skills create asymmetric A/B treatment, propose deleting or updating them

SCORING GUIDANCE:
- Avoid skills that compress scores to ties (e.g., both images scoring 3,3,3,3)
- Tied scores cause default-to-A position bias
- Skills should help DIFFERENTIATE between images using the full 1-4 scale

TIE HANDLING:
- Ground truth contains ~13% ties. The Sub-Agent currently predicts 0% ties
- Consider adding guidance for when "tie" is the correct prediction

LIBRARY HEALTH:
- More skills is NOT always better — too many dilute attention and create conflicts
- Use "action": "delete" for skills that are redundant, contradictory, or harmful
- Before proposing a new skill, check if it contradicts existing skills
- Prefer FEWER, HIGHER-QUALITY skills over accumulation
- When two skills give OPPOSING guidance (e.g., quality-first vs instruction-first), propose merging them into one skill with clear priority rules

IMPORTANT — Tools are CRITICAL for accuracy:
- Tools give the Sub-Agent specialized visual analysis capabilities it cannot do with text reasoning alone
- Examples: OCR text reader, color histogram comparator, object detector, spatial layout analyzer, artifact detector, face/body part detector
- Each Tool is a separate VLM call with a focused system_prompt that extracts structured data from images
- The Sub-Agent can call Tools during evaluation to get objective measurements before making judgments
- You MUST propose at least one Tool if the current library has fewer than 3 tools
- When incorrect predictions stem from visual analysis failures (missed objects, wrong colors, spatial errors), a Tool is almost always the right fix

How the Sub-Agent calls Tools at runtime:
1. Router injects tool descriptions into the system prompt under "# AVAILABLE TOOLS"
2. Sub-Agent outputs a tool call in this exact format:
   <tool>{{"name": "<tool-name>", "images": ["<base64>"], "query": "<question>"}}</tool>
3. The tool's system_prompt is sent to a VLM endpoint along with the images and query
4. The VLM response (JSON) is returned to the Sub-Agent as: <obs>{{...result...}}</obs>
5. Sub-Agent uses the observation to inform its final <answer>

So when you design a Tool:
- system_prompt should instruct a VLM to analyze specific visual aspects and return structured JSON
- content_md should explain WHEN to use the tool and WHAT it returns, so the Sub-Agent knows when to call it
- input_schema: always {{"images": "list[base64_str]", "query": "str"}}
- output_schema: describe the JSON keys the VLM will return (e.g. {{"objects_found": "list[str]", "count": "int"}})
'''


class ChainAnalyzer:
    def __init__(self, model: str = "gemini-3.1-pro-preview"):
        self.model = model

    def _format_example(self, ex: dict) -> str:
        """Format a single example for the analysis prompt."""
        status = "CORRECT" if ex.get("correct") else "INCORRECT"
        return (
            f"--- Example (group_id={ex.get('group_id', 'N/A')}, {status}) ---\n"
            f"Prompt: {ex.get('prompt', 'N/A')}\n"
            f"Ground Truth: {ex.get('gt', 'N/A')}\n"
            f"Prediction: {ex.get('prediction', 'N/A')}\n"
            f"Reasoning Chain:\n{ex.get('reasoning_chain', 'N/A')}\n"
        )

    def analyze(self, examples: list, current_library: dict) -> dict:
        """Analyze all train split results and produce improvement signals.

        Args:
            examples: List of dicts with keys:
                - prompt: editing instruction text
                - gt: ground truth label ("A"/"B"/"tie")
                - prediction: Sub-Agent's prediction ("A"/"B"/"tie")
                - correct: bool
                - reasoning_chain: full multi-turn output text
                - group_id: optional group identifier
            current_library: {skills: [{name, description}], tools: [{name, description}]}

        Returns:
            improvement_signals dict with skill_updates, tool_updates, analysis_summary
        """
        examples_text = "\n".join(self._format_example(ex) for ex in examples)

        skills_summary = json.dumps(current_library.get("skills", []), indent=2)
        tools_summary = json.dumps(current_library.get("tools", []), indent=2)

        prompt = ANALYSIS_PROMPT.format(
            skills_summary=skills_summary,
            tools_summary=tools_summary,
            examples_text=examples_text
        )

        # Retry with backoff for 429 rate limit errors
        response_text = None
        for attempt in range(4):
            try:
                response_text = call_gemini(
                    user_message=prompt,
                    model=self.model,
                    system="You are a JSON-only analyst. You MUST respond with ONLY a valid JSON object. No preamble, no explanation, no markdown fences — just raw JSON. Start your response with '{'.",
                    max_tokens=16384,
                    response_mime_type="application/json",
                )
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str and attempt < 3:
                    wait = (attempt + 1) * 15
                    logger.warning("ChainAnalyzer 429 rate limit, retrying in %ds (attempt %d/4)", wait, attempt + 1)
                    time.sleep(wait)
                    continue
                logger.error("ChainAnalyzer Gemini API call failed: %s", err_str[:200])
                return {
                    "skill_updates": [],
                    "tool_updates": [],
                    "analysis_summary": f"Gemini API unavailable: {err_str[:100]}"
                }
        if response_text is None:
            return {"skill_updates": [], "tool_updates": [], "analysis_summary": "All retries exhausted"}

        # Extract JSON from response — try multiple strategies
        json_text = response_text.strip()

        # Strategy 1: fenced code block
        fenced = re.findall(r"```(?:json)?\s*\n(.*?)```", response_text, re.DOTALL)
        if fenced:
            json_text = fenced[-1].strip()

        # Strategy 2: find first { to last } (raw JSON object)
        if not json_text.startswith("{"):
            start = json_text.find("{")
            end = json_text.rfind("}")
            if start != -1 and end > start:
                json_text = json_text[start:end + 1]

        try:
            signals = json.loads(json_text)
        except json.JSONDecodeError:
            logger.error("Failed to parse chain analysis response as JSON: %s",
                         response_text[:300])
            signals = {
                "skill_updates": [],
                "tool_updates": [],
                "analysis_summary": f"Failed to parse response: {response_text[:200]}"
            }

        # Validate top-level structure
        if "skill_updates" not in signals:
            signals["skill_updates"] = []
        if "tool_updates" not in signals:
            signals["tool_updates"] = []
        if "analysis_summary" not in signals:
            signals["analysis_summary"] = ""

        # Validate individual entries and drop malformed ones
        signals["skill_updates"] = self._validate_skill_updates(signals["skill_updates"])
        signals["tool_updates"] = self._validate_tool_updates(signals["tool_updates"])

        return signals

    def _validate_skill_updates(self, updates: list) -> list:
        """Filter skill_updates to only well-formed entries."""
        valid = []
        for u in updates:
            action = u.get("action")
            name = u.get("name")
            if not action or not name:
                logger.warning("Dropping skill_update with missing action/name: %s", u)
                continue
            if action == "add":
                if not u.get("description") or not u.get("content_md"):
                    logger.warning("Dropping skill 'add' missing description/content_md: %s", name)
                    continue
            elif action == "update":
                if not u.get("content_md"):
                    logger.warning("Dropping skill 'update' missing content_md: %s", name)
                    continue
            elif action == "delete":
                pass  # only name is required
            else:
                logger.warning("Unknown skill action '%s' for '%s', dropping", action, name)
                continue
            valid.append(u)
        return valid

    def _validate_tool_updates(self, updates: list) -> list:
        """Filter tool_updates to only well-formed entries.

        For 'add' action, system_prompt is required (the evolver needs it to
        validate and register the tool).
        """
        valid = []
        for u in updates:
            action = u.get("action")
            name = u.get("name")
            if not action or not name:
                logger.warning("Dropping tool_update with missing action/name: %s", u)
                continue
            if action == "add":
                if not u.get("system_prompt"):
                    logger.warning("Dropping tool 'add' missing system_prompt: %s", name)
                    continue
                if not u.get("description"):
                    logger.warning("Dropping tool 'add' missing description: %s", name)
                    continue
            elif action == "update":
                if not u.get("system_prompt"):
                    logger.warning("Dropping tool 'update' with no system_prompt: %s", name)
                    continue
            elif action == "delete":
                pass  # only name is required
            else:
                logger.warning("Unknown tool action '%s' for '%s', dropping", action, name)
                continue
            valid.append(u)
        return valid
