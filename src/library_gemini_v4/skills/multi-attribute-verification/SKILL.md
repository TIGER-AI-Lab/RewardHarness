---
description: Guidelines for verifying objects that require multiple specific attributes
  or details.
name: multi-attribute-verification
type: skill
---

# Multi-Attribute Verification

When a prompt asks to transform an object into something with multiple specific attributes (e.g., "clear plastic bottle with a nipple", "yellow polka dots"):

1. **Deconstruct the Target**: Break down the requested object into its core attributes.
   - *Example*: "clear plastic bottle with a nipple" -> 1. clear, 2. plastic, 3. bottle, 4. with a nipple.
   - *Example*: "yellow polka dots" -> 1. yellow color, 2. polka dot pattern.
2. **Verify Each Attribute**: Check the edited images for *every single* attribute. Do not just glance at the overall shape.
3. **Identify Partial Success**: If an image makes the object a "clear plastic bottle" but misses the "nipple", it is an incomplete edit.
4. **Score Accordingly**: An image that captures all attributes perfectly should score much higher on Instruction Following than one that misses key details, even if the overall visual quality is good.
