---
description: How to verify complex object replacements and specific attributes.
name: object-attribute-verification
type: skill
---

# Object Attribute Verification

When a prompt asks to replace an object or add an object with specific attributes (e.g., "clear plastic bottle with a nipple", "snow goggles on the man"), break down the instruction into a checklist:

1. **Target Identification**: Was the correct object/person modified? (e.g., Did the man get the goggles, or the woman?)
2. **Complete Replacement**: Is the original object fully removed without ghosting?
3. **Attribute Checklist**: Verify *every* adjective. If the prompt says "clear plastic bottle with a nipple", you must verify: 1) It's a bottle, 2) It's clear plastic, 3) It has a nipple. Missing an attribute reduces the Instruction Following score.
4. **Physical Interaction**: Does the new object fit naturally into the scene? (e.g., Is the hand gripping it correctly?)

**Strategy**: Do not assume an image followed the instruction just because the main object changed. Query the specific attributes explicitly.
