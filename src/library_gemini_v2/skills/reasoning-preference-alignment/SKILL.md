---
description: Ensures the final preference logically matches the comparative analysis
  in the reasoning chain.
name: reasoning-preference-alignment
type: skill
---

# Reasoning-Preference Alignment
Your final `preference` must logically follow from your `reasoning`.

- **Contradiction Check**: Before outputting the preference, review your reasoning. If your reasoning states 'Image A's plausibility and realism are slightly superior' and both images score equally on instruction following, your preference MUST be 'A'.
- **Tie-Breaking**: If both images follow the instruction equally well (or equally poorly), the tie must be broken by visual quality, realism, and lack of artifacts. The image you explicitly praise more in the reasoning must be the one you select as the preference.
