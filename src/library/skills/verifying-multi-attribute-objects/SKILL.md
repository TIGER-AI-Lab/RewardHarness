---
description: Guidelines for evaluating prompts that request objects with multiple
  specific attributes (e.g., material, color, specific parts).
name: verifying-multi-attribute-objects
type: skill
---

# Verifying Multi-Attribute Objects

When a prompt requests an object with multiple specific attributes (e.g., "dark, aged metal with glowing green highlights", "clear plastic bottle with a nipple"):

1. **Deconstruct the Prompt**: Break down the request into individual attributes.
   - Example: "clear plastic bottle with a nipple" -> 1) clear plastic bottle, 2) has a nipple.
   - Example: "dark, aged metal with glowing green highlights" -> 1) dark metal, 2) aged texture, 3) glowing green highlights.
2. **Verify Every Attribute**: Check each image for ALL attributes. An image that misses a key attribute (e.g., missing the nipple, missing the green glow) has failed the instruction and should receive a lower instruction score (e.g., 2).
3. **Use Tools**: If unsure, use the `target-object-verifier` tool to ask specific questions about the presence of these attributes.
4. **Avoid Hallucinations**: Do not assume an attribute is present just because the main object is there. Look closely at the details.
