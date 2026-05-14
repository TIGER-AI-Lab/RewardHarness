---
description: Guidelines for evaluating the addition or modification of text in images.
name: evaluating-text-additions
type: skill
---

# Evaluating Text Additions
When a prompt asks to add or change text (e.g., "Add the word 'begging'", "Add the letters 'CBS'"):
1. **Exact Spelling**: Verify that the text in the image matches the prompt EXACTLY. Misspellings (e.g., "beging" instead of "begging") are severe instruction-following failures. Use visual QA tools to read the exact text.
2. **Legibility and Clarity**: The text must be readable. Distorted, stretched, or blurry text reduces both instruction following and visual quality scores.
3. **Integration**: The text should look like it belongs in the scene. It should match the perspective, lighting, and texture of the surface it is placed on, rather than looking like a flat digital overlay.
4. **Unintended Characters**: Check for extra characters, punctuation, or gibberish added around the requested text.
