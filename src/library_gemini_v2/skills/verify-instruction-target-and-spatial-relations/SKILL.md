---
description: Ensures edits are applied to the exact target, strictly enforcing spatial
  prepositions (under, behind) and prioritizing correct placement over natural integration.
name: verify-instruction-target-and-spatial-relations
type: skill
---

# Verify Instruction Target and Spatial Relations

1. **Strict Spatial Enforcement**: Words like "under", "behind", "in front of", and "next to" must be interpreted literally.
2. **Do Not Dilute for Naturalness**: If the prompt says "put the cat's foot under the bag", the foot must be clearly underneath the bag. Do not prefer an image where the foot is just "tucked near" the bag because it looks "more natural". A forced but correct spatial placement beats a natural but incorrect one.
3. **Target Verification**: Ensure the edit is applied to the exact object specified, not a neighboring object.
