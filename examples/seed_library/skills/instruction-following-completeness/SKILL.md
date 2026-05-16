---
name: instruction-following-completeness
type: skill
description: Score completeness of instruction execution. Partial edits get partial credit; missed sub-steps cost points.
---

# Instruction Following Completeness

Many editing prompts contain multiple sub-instructions. Evaluate each one independently and aggregate.

## Decomposition

First parse the prompt into atomic sub-instructions. Examples:

- "Replace the red car with a blue bicycle" → (1) remove red car, (2) place blue bicycle in approximately the same location.
- "Add a 'Sale' sign and change the storefront to red" → (1) add sign with correct text, (2) recolor storefront.
- "Make the computer have a futuristic design" → (1) keep the computer recognizable, (2) apply futuristic styling.

## Scoring (per candidate, 1–4)

- **4 — Complete:** All sub-instructions executed faithfully. No omissions.
- **3 — Mostly complete:** All sub-instructions attempted but one is partially executed (e.g., color changed but shape slightly wrong).
- **2 — Partial:** At least one sub-instruction skipped entirely, or one is wrong (wrong object, wrong color, wrong location).
- **1 — Failed:** Two or more sub-instructions missed, or the edit went in an unrelated direction.

## When in doubt

If both candidates are at score 3 or both at score 2, fall back to which one feels closer to what a human would call "correct" given the prompt. Then break ties with `realism-and-artifact-penalties`.
