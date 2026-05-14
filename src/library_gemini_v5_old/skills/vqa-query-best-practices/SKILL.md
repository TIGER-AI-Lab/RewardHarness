---
description: Guidelines for formulating effective, objective queries for the Visual
  Question Answering tool.
name: vqa-query-best-practices
type: skill
---

When using the `visual-question-answering` tool, you MUST NOT delegate subjective judgments or evaluation criteria to the tool. The tool acts as your "eyes", not your "brain".

1. **Ask Objective, Descriptive Questions**:
   - **BAD**: "Did Image A follow the instruction?" or "Is the background changed unnecessarily?" or "Which image is more realistic?"
   - **GOOD**: "What objects are in the background of Image A?" or "Describe the texture of the game assets in Image B." or "Are the original trees still present in Image A?"

2. **Break Down Complex Queries**:
   - **BAD**: "Is the home plate visible in front of the catcher?" (If it's small, the tool might miss it).
   - **GOOD**: "Describe the ground area directly in front of the catcher's feet. Is there a white shape there?"

3. **Counting and Spatial Relations**:
   - **BAD**: "Is the text on the 4th surfboard?"
   - **GOOD**: "List the surfboards from left to right and describe what is written on each one."

4. **Artifact Detection**:
   - **BAD**: "Are there artifacts?"
   - **GOOD**: "Look closely at the man's hands and face. Are there any extra fingers, blurred lines, or distorted features?"
