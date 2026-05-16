"""Sub-Agent for RewardHarness pipeline.

Qwen2.5-VL-7B-Instruct via vLLM for multi-turn visual reasoning.
Receives Router-injected skill/tool context, performs tool dispatch via Library.call_tool.
"""

import json
import os
import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

logger = logging.getLogger(__name__)

# SCORE_TEMPLATES_DIR resolves relative to src/, so it works in a source
# checkout (where score-guidelines/ sits at the repo root, two levels up).
# For wheel/sdist installs we include score-guidelines via MANIFEST.in;
# users can override the path with the REWARDHARNESS_TEMPLATES_DIR env var.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORE_TEMPLATES_DIR = os.environ.get(
    "REWARDHARNESS_TEMPLATES_DIR",
    os.path.join(PROJECT_ROOT, "score-guidelines"),
)
MAX_TOOL_CALLS = 5

BASE_INSTRUCTIONS_NO_TOOLS = """You are an expert image editing quality evaluator comparing two edited images (A and B) against a source image.

Think step by step using <think>...</think> tags.

## Output Format

When you are ready to give your verdict, output your final answer as:
<answer>
{
  "preference": "A" or "B" or "tie",
  "score_A_instruction": <integer 1-4>,
  "score_A_quality": <integer 1-4>,
  "score_B_instruction": <integer 1-4>,
  "score_B_quality": <integer 1-4>,
  "reasoning": "<brief explanation>"
}
</answer>

The answer body must be valid JSON. All score values must be integers from 1 to 4. The "preference" field must be exactly "A", "B", or "tie".

Score BOTH images on BOTH scoring templates (Instruction Following and Visual Quality), then output your <answer>."""

TOOL_INSTRUCTIONS = """

### Tool calls
To call a visual analysis tool, output exactly ONE tool call per turn:
<tool>
{"name": "<tool-name>", "images": ["<base64-string>"], "query": "<your question>"}
</tool>

The tool call body must be valid JSON with these fields:
- "name" (string): the tool name
- "images" (list of strings): base64-encoded image(s) to analyze
- "query" (string): your analysis question

### Tool observations
After a tool returns, you will see the result wrapped as:
<obs>{...json result...}</obs>

You may call tools if available, or go directly to your <answer>."""

FALLBACK_ANSWER = {
    "preference": "tie",
    "score_A_instruction": 2, "score_A_quality": 2,
    "score_B_instruction": 2, "score_B_quality": 2,
    "reasoning": "fallback: unable to parse model output"
}


class SubAgent:
    def __init__(self, library, endpoint_pool, max_retries: int = 3):
        self.library = library
        self.endpoint_pool = endpoint_pool
        self.max_retries = max_retries

    def _call_vllm(self, messages: list, max_tokens: int = 2048) -> str:
        """Call vLLM with exponential backoff retry.

        Returns:
            Model response text. Empty string if model returns None content.

        Raises:
            Exception: After all retries are exhausted.
        """
        for attempt in range(self.max_retries):
            try:
                endpoint = self.endpoint_pool.next()
                client = OpenAI(base_url=endpoint, api_key="token")
                resp = client.chat.completions.create(
                    model="Qwen2.5-VL-7B-Instruct",
                    messages=messages,
                    max_tokens=max_tokens,
                )
                content = resp.choices[0].message.content
                if content is None:
                    logger.warning("vLLM returned None content on attempt %d", attempt + 1)
                    return ""
                return content
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning("vLLM call failed (attempt %d): %s, retrying in %ds",
                                   attempt + 1, e, wait)
                    time.sleep(wait)
                else:
                    logger.error("vLLM call failed after %d attempts: %s",
                                 self.max_retries, e)
                    raise

    def _parse_tool_call(self, text: str) -> dict | None:
        """Extract tool call from <tool>...</tool> tags.

        Handles multiline JSON, surrounding whitespace, and nested braces.
        """
        match = re.search(r'<tool>\s*(.*?)\s*</tool>', text, re.DOTALL)
        if not match:
            return None
        raw = match.group(1).strip()
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                logger.warning("Tool call content is not a JSON object: %s", type(parsed))
                return None
            if "name" not in parsed:
                logger.warning("Tool call missing required 'name' field")
                return None
            return parsed
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse tool call JSON: %s -- raw: %.200s", e, raw)
            return None

    def _parse_answer(self, text: str) -> dict | None:
        """Extract answer from <answer>...</answer> tags.

        Validates all required fields and score ranges (1-4).
        Returns None on any parse or validation failure.
        """
        match = re.search(r'<answer>\s*(.*?)\s*</answer>', text, re.DOTALL)
        if not match:
            return None
        raw = match.group(1).strip()
        try:
            answer = json.loads(raw, strict=False)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse answer JSON: %s -- raw: %.200s", e, raw)
            return None

        required_scores = ["score_A_instruction", "score_A_quality",
                           "score_B_instruction", "score_B_quality"]
        if "preference" not in answer:
            logger.warning("Answer missing 'preference' field")
            return None
        if answer["preference"] not in ("A", "B", "tie"):
            logger.warning("Invalid preference value: %s", answer["preference"])
            return None
        for key in required_scores:
            if key not in answer:
                logger.warning("Answer missing required field: %s", key)
                return None
            try:
                val = int(answer[key])
            except (TypeError, ValueError):
                logger.warning("Score field '%s' is not an integer: %s", key, answer[key])
                return None
            if val < 1 or val > 4:
                logger.warning("Score field '%s' out of range [1,4]: %d", key, val)
                return None
            answer[key] = val  # normalize to int (model may return float)
        return answer

    def evaluate(self, source_img: str, edited_A: str, edited_B: str,
                 prompt: str, skill_context: str) -> dict:
        """Evaluate a pair of edited images.

        Args:
            source_img: base64 encoded source image
            edited_A: base64 encoded edited image A
            edited_B: base64 encoded edited image B
            prompt: editing instruction text
            skill_context: assembled L2 context from Router (may be empty)

        Returns:
            dict with preference, scores, reasoning, and full chain
        """
        # 1. Load fixed templates (use context managers to avoid file handle leaks)
        t1_path = os.path.join(SCORE_TEMPLATES_DIR, "template1_instruction_following.md")
        t2_path = os.path.join(SCORE_TEMPLATES_DIR, "template2_visual_quality.md")
        with open(t1_path) as f:
            t1 = f.read().replace("{text_prompt}", prompt)
        with open(t2_path) as f:
            t2 = f.read().replace("{text_prompt}", prompt)
        fixed_templates = f"# SCORE TEMPLATE: INSTRUCTION FOLLOWING\n{t1}\n\n# SCORE TEMPLATE: VISUAL QUALITY\n{t2}"

        # 2. Assemble system prompt — only include tool instructions if tools exist
        has_tools = skill_context and "# AVAILABLE TOOLS" in skill_context
        system_prompt = BASE_INSTRUCTIONS_NO_TOOLS
        if has_tools:
            system_prompt += TOOL_INSTRUCTIONS
        system_prompt += "\n\n" + fixed_templates
        if skill_context:
            system_prompt += "\n\n" + skill_context

        # 3. Build user message with images
        user_msg = "Evaluate both edited images against the source."
        if has_tools:
            user_msg += " Use tools if needed, then provide your <answer>."
        else:
            user_msg += " Provide your <answer>."
        user_content = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{source_img}"}},
            {"type": "text", "text": "Source image (above)"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{edited_A}"}},
            {"type": "text", "text": "Edited image A (above)"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{edited_B}"}},
            {"type": "text", "text": "Edited image B (above)"},
            {"type": "text", "text": f"Editing instruction: {prompt}\n\n{user_msg}"},
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        # 4. Multi-turn loop
        #    - turn 0..MAX_TOOL_CALLS-1: may dispatch tools
        #    - turn MAX_TOOL_CALLS: final chance — answer only, no more tools
        #    On each turn: if <answer> found, return immediately.
        #    If <tool> found and turns remain, dispatch. Otherwise break to fallback.
        chain_parts = []
        for turn in range(MAX_TOOL_CALLS + 1):
            try:
                output = self._call_vllm(messages)
            except Exception as e:
                logger.error("vLLM call failed in multi-turn loop (turn %d): %s", turn, e)
                break
            chain_parts.append(output)

            # Check for answer first (takes priority over tool calls)
            answer = self._parse_answer(output)
            if answer is not None:
                answer["chain"] = "\n".join(chain_parts)
                return answer

            # Check for tool call
            tool_call = self._parse_tool_call(output)
            if tool_call is not None and turn < MAX_TOOL_CALLS:
                tool_name = tool_call.get("name", "")
                try:
                    tool_result = self.library.call_tool(
                        tool_name,
                        {"images": tool_call.get("images", []),
                         "query": tool_call.get("query", "")},
                        self.endpoint_pool
                    )
                    obs = json.dumps(tool_result)
                except Exception as e:
                    logger.warning("Tool '%s' call failed: %s", tool_name, e)
                    obs = json.dumps({"error": str(e)})

                # Append assistant output and observation, continue loop
                messages.append({"role": "assistant", "content": output})
                messages.append({"role": "user", "content": f"<obs>{obs}</obs>"})
            elif tool_call is not None and turn >= MAX_TOOL_CALLS:
                # Tool call requested but no turns remaining -- break to fallback
                logger.warning("Tool call requested on final turn %d, breaking to fallback", turn)
                break
            else:
                # Output had neither <answer> nor <tool> -- break to fallback
                logger.warning("No <answer> or <tool> found on turn %d, breaking to fallback", turn)
                break

        # Fallback: return tie with neutral scores
        logger.info("Falling back to default answer after %d chain parts", len(chain_parts))
        fallback = dict(FALLBACK_ANSWER)
        fallback["chain"] = "\n".join(chain_parts)
        return fallback

    def batch_evaluate(self, examples: list, skill_contexts: list,
                       max_workers: int = 128) -> list:
        """Batch evaluate examples concurrently.

        Args:
            examples: list of dicts with source_img, edited_A, edited_B, prompt (all base64/str)
            skill_contexts: list of context strings (one per example, from Router)
            max_workers: ThreadPoolExecutor workers

        Returns:
            list of result dicts in same order as examples.
            Failed evaluations return FALLBACK_ANSWER; exceptions never crash other threads.
        """
        results = [None] * len(examples)

        def _eval(idx):
            ex = examples[idx]
            ctx = skill_contexts[idx] if idx < len(skill_contexts) else ""
            return self.evaluate(
                source_img=ex["source_img"],
                edited_A=ex["edited_A"],
                edited_B=ex["edited_B"],
                prompt=ex["prompt"],
                skill_context=ctx
            )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {executor.submit(_eval, i): i
                             for i in range(len(examples))}
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    logger.error("batch_evaluate error for example %d: %s",
                                 idx, e, exc_info=True)
                    fallback = dict(FALLBACK_ANSWER)
                    fallback["chain"] = f"error: {e}"
                    results[idx] = fallback

        return results
