---
description: Evaluating broad thematic changes, style transfers, and environmental
  modifications while preserving structure.
name: thematic-and-style-transformation
type: skill
---

When evaluating prompts that change the style, theme, or background (e.g., "make it a sold out concert", "mosaic-tile style", "grassy savannah"):

1. **Structure Preservation (Crucial)**: A high-quality style transfer or background change MUST preserve the core structure, layout, and identity of the main subjects unless explicitly told otherwise.
   - **Over-editing**: If an image completely replaces the original scene with a generic stock photo, changes the identity/pose of the main subject, or removes key foreground elements, it should be heavily penalized.
2. **Thematic Accuracy**: Does the new style/background contain the specific elements requested? (e.g., "sold out concert" needs a crowd and stage lighting; "child's bedroom" needs toys, a bed, etc.).
3. **Integration and Blending**: The foreground subjects must blend naturally with the new background. Look for harsh edges, mismatched lighting, or floating objects.
4. **Style Consistency**: For artistic styles (e.g., "mosaic-tile"), the style should be applied uniformly across the specified areas without leaving patches of the original photo unedited, but without distorting the underlying shapes beyond recognition.
