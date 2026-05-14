"""Show the SubAgent reasoning-chain format used at inference time.

The frozen VLM Sub-Agent produces interleaved <think>, <tool>, <obs>, and
<answer> tags. This script prints a representative example of what one full
preference judgment looks like, so you know what to expect when running
`scripts/run_benchmark.py` or `scripts/run_evolution.py`.

No external calls; safe to run with just stdlib.
"""

import textwrap


EXAMPLE_CHAIN = """\
<think>
The prompt asks to add a "Sale" sign on the storefront. I need to check three
criteria for each candidate:
  1. Does the sign actually appear?
  2. Is the text spelled correctly?
  3. Does the rest of the storefront look unchanged (no over-editing)?
Let me call the OCR tool to verify spelling.
</think>

<tool>
{"name": "text-and-ocr-analyzer",
 "images": ["<base64-A>", "<base64-B>"],
 "query": "What text appears in each image? Spell it exactly."}
</tool>

<obs>
{"image_1_text": "Sale", "image_1_spelling_correct": true,
 "image_2_text": "Sael", "image_2_spelling_correct": false}
</obs>

<think>
Candidate A spells "Sale" correctly. Candidate B has a typo ("Sael"). Both
sign placements look natural, but B's typo is a clear instruction-following
failure for an "add a Sale sign" prompt. The rest of both storefronts look
preserved.
</think>

<answer>
{
  "preference": "A",
  "score_A_instruction": 4,
  "score_A_quality": 4,
  "score_B_instruction": 2,
  "score_B_quality": 3,
  "reasoning": "A correctly adds 'Sale'; B has a typo 'Sael'."
}
</answer>
"""


def main():
    print("RewardHarness Sub-Agent reasoning chain — example output")
    print("=" * 64)
    print(textwrap.dedent("""
        Tag legend:
          <think>   internal reasoning, ignored by the scorer
          <tool>    optional structured call to a Tool from the Library
          <obs>     tool result injected back into the chain
          <answer>  final JSON verdict — the only part read by the pipeline
    """))
    print("Example trace (one preference judgment):")
    print("-" * 64)
    print(EXAMPLE_CHAIN)
    print("-" * 64)
    print(textwrap.dedent("""
        Parsing rules (see src/sub_agent.py):
          - The Sub-Agent is allowed up to N tool calls per judgment
            (default: 3), bounded by config.
          - If no <answer> is emitted, FALLBACK_ANSWER is used (tie, 2/2/2/2).
          - The "preference" field must be exactly "A", "B", or "tie".
          - All four score fields must be integers in [1, 4].

        The evolved library (in src/library/) determines which Tools are
        offered and which Skills shape the Sub-Agent's rubric application.
    """))


if __name__ == "__main__":
    main()
