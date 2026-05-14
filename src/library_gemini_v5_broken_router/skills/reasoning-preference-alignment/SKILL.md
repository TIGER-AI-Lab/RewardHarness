---
description: Ensures the final preference strictly matches the reasoning and assigned
  scores.
name: reasoning-preference-alignment
type: skill
---

# Reasoning and Preference Alignment

When evaluating images, your final `preference` MUST logically follow from your `reasoning` and the scores you assign. 

**Failure Mode:**
In some cases, the reasoning explicitly states that Image A is better (e.g., "Image A's plausibility and realism are slightly superior"), but the output preference is incorrectly set to "B".

**Guidance:**
1. **Review your reasoning:** Before outputting the final JSON, ensure you know which image you concluded is better.
2. **Check your scores:** The image with the higher combined instruction and quality scores should generally be your preference.
3. **Consistency:** If you write "Image A is more realistic and follows the instruction better", your preference MUST be "A".
