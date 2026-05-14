---
description: Evaluating whether the edit is exclusive to the requested changes, specifically
  checking for global bleed.
name: exclusivity-and-preservation
type: skill
---

# Exclusivity and Preservation Evaluation

When an instruction specifies a localized edit (e.g., "adjust the brightness of the sky", "make the surfboards pink", "remove the person on the left"):

1. **Identify the Target Region**: Determine exactly what the prompt is asking to change.
2. **Check for Global Bleed**: Did the edit affect the entire image? 
   - *Example*: If asked to make the sky sunnier, did the foreground also become overexposed?
   - *Example*: If asked to make surfboards pink, did the background also turn pink?
3. **Check Unintended Alterations**: Were other objects removed, distorted, or changed in color/texture?
4. **Penalize Over-editing**: If an edit bleeds into areas that should have been preserved, heavily penalize the "Instruction Following" score (e.g., score 2 or 1). An ideal edit is perfectly isolated to the target subject/region.
