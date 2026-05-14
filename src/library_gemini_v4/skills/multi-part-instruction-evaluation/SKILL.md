---
description: Guidelines for evaluating prompts with multiple distinct requirements,
  ensuring all parts are fulfilled.
name: multi-part-instruction-evaluation
type: skill
---

# Multi-Part Instruction Evaluation
When a prompt contains multiple instructions (e.g., 'Remove X AND increase brightness of Y'):
1. **Deconstruct the Prompt**: Break the prompt down into individual requirements.
2. **Check Each Requirement**: Evaluate the edited images against EVERY requirement.
3. **Partial Compliance**: If an image only fulfills one part of the instruction (e.g., removes the object but fails to increase brightness), it must receive a lower Instruction Following score than an image that fulfills all parts.
4. **Over-editing**: Ensure that fulfilling one requirement didn't unintentionally alter other parts of the image.
