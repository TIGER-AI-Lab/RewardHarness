---
description: Guidelines for evaluating prompts that require adding, modifying, or
  removing text.
name: text-rendering-evaluation
type: skill
---

# Text Rendering Evaluation

When a prompt involves text (e.g., "Add the word 'begging'", "Add the letters 'CBS'"), evaluate the following criteria strictly:

1. **Exact Spelling**: Verify the text matches the prompt exactly. Pay attention to typos, extra letters, missing letters, and case sensitivity. A misspelled word is a major failure in Instruction Following.
2. **Placement**: Check if the text is in the specified location (e.g., "bottom left", "on the 4th surfboard").
3. **Integration and Typography**: Does the text look like it belongs in the scene? Evaluate the font choice, perspective, lighting, and blending. Text that looks like a flat digital overlay on a 3D object should score lower in Visual Quality.
4. **Artifacts**: Ensure the area around the text isn't smudged or distorted.

**Strategy**: Always use a visual question answering tool to explicitly ask "What text is written in Image A?" and "What text is written in Image B?" before making a judgment.
