---
description: How to systematically evaluate prompts with more than one instruction.
name: evaluating-multiple-constraints
type: skill
---

# Evaluating Multiple Constraints
When a prompt contains multiple distinct instructions (e.g., "Remove X AND brighten Y", "Change A to B WITH a C"):
1. **Deconstruct the Prompt**: Break the prompt down into a checklist of atomic constraints.
   - Example: "Change the Wii-remote to a clear plastic bottle with a nipple." -> Constraint 1: Replace Wii-remote with clear plastic bottle. Constraint 2: The bottle must have a nipple.
2. **Evaluate Independently**: Check each edited image against every constraint on the checklist. Use visual analysis tools to verify specific details if unsure.
3. **Strict Prioritization**: An image that successfully fulfills ALL constraints is strictly better than an image that fulfills only some, even if the partially successful image has slightly better visual quality.
4. **Identify Partial Failures**: Explicitly note which constraints were missed (e.g., "Image A added the bottle but forgot the nipple").
