---
description: Ensures edits do not destroy the original image's layout, unedited subjects,
  or art style (penalizes over-editing).
name: structure-and-subject-preservation
type: skill
---

# Structure and Subject Preservation

When evaluating image edits, it is crucial to penalize **over-editing**. An image that follows the text prompt but destroys the original image's structure, background, or unedited subjects is worse than an image that applies a subtle, well-integrated edit.

## Key Checks:
1. **Art Style Preservation**: If the original image is a cartoon, illustration, or painting, the edited image MUST preserve this style. Do not reward images that arbitrarily photorealize a stylized image.
2. **Background and Layout**: The edit should only change what is requested. If the prompt asks to change a specific object (e.g., 'Change the Wii-remote to a bottle'), the hand holding it and the background must remain intact. If the prompt asks to change the setting (e.g., 'sold out concert', 'cafeteria'), the main subjects must remain identical in identity, pose, and structure.
3. **Integration vs. Destruction**: Reward images that seamlessly integrate the requested change without warping, stretching, or degrading the overall image quality. Heavy-handed edits that replace the entire scene unnecessarily should receive lower instruction and quality scores.
