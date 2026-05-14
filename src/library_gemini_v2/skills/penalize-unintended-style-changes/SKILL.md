---
description: Guidelines for penalizing images that alter the original art style when
  not requested, with exceptions for intended drastic changes.
name: penalize-unintended-style-changes
type: skill
---

# Penalize Unintended Style Changes

1. **Identify the Original Style**: Determine if the original image is photorealistic, a painting, a cartoon, 3D render, etc.
2. **Check the Prompt**: Does the prompt explicitly ask for a style change? (e.g., "make it a painting", "in the style of Claes Oldenburg", "mosaic-tile").
3. **Apply Penalties**: If the prompt DOES NOT ask for a style change, heavily penalize images that alter the original style (e.g., turning a real photo into a cartoon or adding unwanted filters).
4. **Exception for Intended Changes**: If the prompt explicitly requests a new style, artist, or drastic setting change, do NOT penalize the image for altering the original art style or losing photorealism. Evaluate it based on how well it achieved the *requested* style.
