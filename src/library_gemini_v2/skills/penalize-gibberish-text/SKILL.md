---
description: Guidelines for penalizing gibberish text, establishing that instruction
  fulfillment strictly outweighs text artifacts.
name: penalize-gibberish-text
type: skill
---

# Penalize Gibberish Text

Gibberish, misspelled, or garbled text is a common artifact in AI image editing and should be penalized, BUT it is a secondary concern compared to instruction fulfillment.

## Hierarchy of Evaluation
1. **Primary Directive (Instruction Fulfillment)**: Did the image follow the main instruction? (e.g., 'Make it look like a subway', 'Change the background to a city').
2. **Secondary Directive (Text Quality)**: Did the image introduce gibberish text?

## Rules
- **Never reward an image that fails the prompt just because it avoided text artifacts.**
- If Image A fails the main instruction (e.g., does not change the setting as requested) but has clean text, and Image B successfully follows the main instruction but introduces gibberish text (e.g., 'Newerg Yyrk' on a sign), **Image B MUST be preferred**.
- Only use gibberish text as a tie-breaker or a reason to penalize when BOTH images successfully follow the main instruction.
