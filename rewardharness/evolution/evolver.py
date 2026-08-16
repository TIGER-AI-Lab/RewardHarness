"""Evolver for RewardHarness pipeline.

Applies improvement signals to Library (add/update Skills and Tools).
Supports snapshot/restore for rollback on val_acc regression.
"""

import json
import logging

from openai import OpenAI

from rewardharness.clients.gemini import call_gemini
from rewardharness.evaluation.engine import SUBAGENT_MODEL

logger = logging.getLogger(__name__)

TOOL_VALIDATION_PROMPT = """You are refining a system prompt for a specialized VLM tool.

The tool "{tool_name}" with description "{tool_description}" had its system_prompt tested on sample images but produced poor results.

Current system_prompt:
{current_prompt}

Sample failures (tool output vs expected behavior):
{failures}

Please provide an improved system_prompt that will produce more reliable, correctly-formatted JSON output.
Return ONLY the improved system_prompt text, nothing else."""


class Evolver:
    def __init__(self, library, endpoint_pool=None, complete=None):
        self.library = library
        self.endpoint_pool = endpoint_pool
        self._complete = complete or call_gemini

    def apply_signals(self, signals: dict) -> dict:
        """Apply improvement signals to Library.

        Args:
            signals: {skill_updates: [...], tool_updates: [...], analysis_summary: str}

        Returns:
            dict with counts of applied changes
        """
        applied = {
            "skills_added": 0,
            "skills_updated": 0,
            "skills_deleted": 0,
            "tools_added": 0,
            "tools_updated": 0,
            "tools_deleted": 0,
        }

        for u in signals.get("skill_updates", []):
            try:
                if u["action"] == "add":
                    self.library.add_skill(u["name"], u["description"], u["content_md"])
                    applied["skills_added"] += 1
                    logger.info(f"Added skill: {u['name']}")
                elif u["action"] == "update":
                    self.library.update_skill(
                        u["name"], u["content_md"], new_description=u.get("description")
                    )
                    applied["skills_updated"] += 1
                    logger.info(f"Updated skill: {u['name']}")
                elif u["action"] == "delete":
                    self.library.delete_skill(u["name"])
                    applied["skills_deleted"] += 1
                    logger.info(f"Deleted skill: {u['name']} (reason: {u.get('reason', 'N/A')})")
            except Exception as e:
                logger.error(f"Failed to apply skill update {u.get('name')}: {e}")

        for u in signals.get("tool_updates", []):
            try:
                if u["action"] == "add":
                    system_prompt = u["system_prompt"]
                    # Validate tool system_prompt with test samples
                    if self.endpoint_pool:
                        system_prompt = self._validate_tool_prompt(
                            name=u["name"],
                            description=u["description"],
                            system_prompt=system_prompt,
                            min_samples=20,
                            max_refinement_rounds=3,
                        )
                    self.library.add_tool(
                        u["name"],
                        u["description"],
                        system_prompt,
                        u.get("input_schema", {}),
                        u.get("output_schema", {}),
                        u.get("content_md", ""),
                    )
                    applied["tools_added"] += 1
                    logger.info(f"Added tool: {u['name']}")
                elif u["action"] == "update":
                    new_prompt = u.get("system_prompt")
                    if not new_prompt:
                        logger.warning(
                            f"Tool update for '{u['name']}' has no system_prompt, skipping"
                        )
                        continue
                    self.library.update_tool(u["name"], new_prompt)
                    applied["tools_updated"] += 1
                    logger.info(f"Updated tool: {u['name']}")
                elif u["action"] == "delete":
                    self.library.delete_tool(u["name"])
                    applied["tools_deleted"] += 1
                    logger.info(f"Deleted tool: {u['name']} (reason: {u.get('reason', 'N/A')})")
            except Exception as e:
                logger.error(f"Failed to apply tool update {u.get('name')}: {e}")

        return applied

    def _validate_tool_prompt(
        self,
        name: str,
        description: str,
        system_prompt: str,
        min_samples: int = 20,
        max_refinement_rounds: int = 3,
    ) -> str:
        """Validate a tool's system_prompt by testing with sample inputs.

        Tests the system_prompt against dummy samples to ensure it produces
        valid JSON output. Refines via Claude if needed.

        Returns the validated (possibly refined) system_prompt.
        """
        for round_num in range(max_refinement_rounds):
            failures = []
            successes = 0

            for i in range(min_samples):
                try:
                    endpoint = self.endpoint_pool.next()
                    client = OpenAI(base_url=endpoint, api_key="token")
                    # Use a simple test query
                    resp = client.chat.completions.create(
                        model=SUBAGENT_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Test query {i}: Analyze as instructed. Return JSON only.",
                                    }
                                ],
                            },
                        ],
                        max_tokens=512,
                    )
                    output = resp.choices[0].message.content or ""
                    # Check if output is valid JSON
                    json.loads(output)
                    successes += 1
                except json.JSONDecodeError:
                    failures.append(f"Sample {i}: output was not valid JSON: {output[:100]}")
                except Exception as e:
                    failures.append(f"Sample {i}: API error: {str(e)[:100]}")

            success_rate = successes / min_samples if min_samples > 0 else 0
            logger.info(
                f"Tool '{name}' validation round {round_num + 1}: "
                f"{successes}/{min_samples} success ({success_rate:.0%})"
            )

            if success_rate >= 0.8:  # 80% threshold
                return system_prompt

            # Refine via Gemini
            if round_num < max_refinement_rounds - 1:
                try:
                    refine_prompt = TOOL_VALIDATION_PROMPT.format(
                        tool_name=name,
                        tool_description=description,
                        current_prompt=system_prompt,
                        failures="\n".join(failures[:5]),
                    )
                    system_prompt = self._complete(
                        user_message=refine_prompt,
                        model="gemini-3.1-pro-preview",
                        max_tokens=1024,
                    )
                    logger.info(f"Refined system_prompt for tool '{name}'")
                except Exception as e:
                    logger.warning(f"Failed to refine prompt via Gemini: {e}")

        logger.warning(
            f"Tool '{name}' validation did not reach threshold, using best effort prompt"
        )
        return system_prompt

    def snapshot(self) -> dict:
        """Capture the repository state for rollback."""
        return self.library.snapshot()

    def restore(self, snap: dict):
        """Restore Library to a previous snapshot state.

        Args:
            snap: snapshot dict from self.snapshot()
        """
        self.library.restore(snap)
        logger.info(f"Restored library to snapshot with {len(snap['registry'])} items")
