---
description: Techniques to prevent hallucinating empty images and mixing up Image
  A and Image B during OCR.
name: verify-image-content-and-ocr
type: skill
---

# Verifying Image Content and OCR
Visual Language Models can sometimes hallucinate image content, swap Image A and Image B, or fail to perceive dark images.

## Rules for Robust Perception:
1. **The "Black Screen" Fallacy**: Never dismiss an image as "having no content" or being a "black screen" unless you are absolutely certain. Often, the image is just very dark (e.g., a dark sci-fi UI) or the edit removed the background but kept the assets. Look closely at the pixel details.
2. **Image Swapping**: When comparing specific features (especially text/OCR), explicitly ground your observation to avoid swapping A and B. 
   - *Bad*: "Image A has '8' and Image B has 'CBS'." (Prone to swapping).
   - *Good*: "Looking at the left image (A), the text on the surfboard is [X]. Looking at the right image (B), the text is [Y]." Take a moment to double-check which image is which.
3. **Subtle Object Recognition**: If an object looks slightly different than expected (e.g., a baby bottle instead of a generic water bottle), do not immediately claim the model "failed to add the object." It might be a stylistically different version of the requested object. Evaluate its plausibility in the context of the scene.
