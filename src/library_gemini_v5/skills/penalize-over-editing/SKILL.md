---
description: Guidelines for heavily penalizing images that follow the instruction
  but introduce destructive, unintended changes to the original image.
name: penalize-over-editing
type: skill
---

# Penalizing Over-editing
When evaluating image edits, the "Do No Harm" principle is critical. An edit that follows the instruction but ruins the rest of the image is worse than an edit that is subtle or partially successful but preserves the original image.

## Key Failure Modes to Penalize:
1. **Style Shift**: The prompt asks for a setting change (e.g., "school cafeteria"), but the model changes a photorealistic image into a cartoon or 3D render.
2. **Hallucinated Objects**: The prompt asks to modify an object (e.g., "rotate the bag"), but the model adds new parts that weren't there (e.g., adding handles or labels to a plain bag).
3. **Subject Corruption**: The prompt asks for a global style transfer (e.g., "mosaic-tile style"), but applying it to a person's face or body makes it look grotesque or unrecognizable. Preserving the main subject's integrity is often preferred.
4. **Loss of Original Identity**: The prompt asks for a specific location (e.g., "New York subway"), but the model introduces elements from a completely different location (e.g., European train branding).

## Evaluation Rule:
If Image A has a minor flaw in following the instruction (e.g., a typo in text, or a less dramatic background change) but perfectly preserves the original image's structure and style, and Image B perfectly follows the instruction but introduces severe over-editing or style shifts, **prefer Image A**.
