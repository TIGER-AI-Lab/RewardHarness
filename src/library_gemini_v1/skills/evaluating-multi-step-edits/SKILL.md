---
description: Guidelines for evaluating prompts with multiple distinct instructions.
name: evaluating-multi-step-edits
type: skill
---

# Evaluating Multi-Step Edits
When a prompt contains multiple instructions (e.g., "Remove the object on the left AND increase the brightness of the central figure"):
1. **Deconstruct the Prompt**: Break the prompt down into its individual components.
2. **Check Each Component**: Evaluate whether each edited image successfully completes *every* component.
3. **Partial Success**: If an image only completes one of the two instructions, it should receive a lower Instruction Following score (e.g., 2 or 3) compared to an image that completes both.
4. **Over-editing**: Ensure that global adjustments (like brightness) are only applied to the specified areas (e.g., "central figure") and not the entire image, unless requested.
