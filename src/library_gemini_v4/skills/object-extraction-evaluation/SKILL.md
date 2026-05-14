---
description: Guidelines for evaluating prompts that request extracting a subject and
  removing the background, emphasizing subject preservation.
name: object-extraction-evaluation
type: skill
---

# Object Extraction Evaluation
When evaluating prompts that ask to extract a subject or remove the background:
1. **Background Removal**: The background should be completely removed (usually replaced with white, transparent, or a solid color) without leaving messy edges.
2. **Subject Preservation (Critical)**: The extracted subject MUST remain exactly the same as in the source image. If the subject's clothing, face, pose, or accessories change (e.g., a white jacket becomes a black jacket), this is a severe violation of Exclusivity of Edit and Semantic Accuracy.
3. **Edge Quality**: Check for jagged edges, missing parts of the subject, or leftover background fragments.
