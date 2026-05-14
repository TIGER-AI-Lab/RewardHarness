---
description: Mandates strict verification of which image contains which features to
  prevent attributing Image A's details to Image B.
name: prevent-image-feature-swapping
type: skill
---

# Prevent Image Feature Swapping

Positional hallucination—where the evaluator attributes Image A's features, text, or artifacts to Image B, or vice versa—is a critical failure mode.

## Guidelines
1. **Independent Verification**: Always describe Image A's features explicitly and independently before looking at Image B. Do not blend their descriptions.
2. **Use Tools for Confirmation**: If the prompt involves specific text (e.g., 'Newerg Yyrk'), small objects (e.g., a nipple on a bottle, a home plate), or specific artifacts, you MUST use the `side-by-side-image-comparator` or `visual-question-answering` tool to confirm exactly which image contains the feature.
3. **Double-Check Claims**: If you find yourself writing 'Image A lacks X' but another part of your reasoning suggests Image A has X, stop and re-verify. 
4. **Text and Spelling**: When evaluating text additions, explicitly write out the spelling found in Image A and Image B. Do not assume one is correct without checking.
