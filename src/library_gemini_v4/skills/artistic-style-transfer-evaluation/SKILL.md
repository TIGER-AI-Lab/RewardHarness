---
description: Guidelines for evaluating prompts that request a change in artistic style
  (e.g., specific artists, mediums).
name: artistic-style-transfer-evaluation
type: skill
---

# Artistic Style Transfer Evaluation

When evaluating prompts that ask to change the image to a specific artistic style (e.g., "Make it look like Gustav Klimt drew it", "Transfer into a mosaic-tile style"):

1. **Style Accuracy**: Does the image genuinely reflect the requested style? Look for specific hallmarks of the artist or medium (e.g., Klimt's gold leaf and geometric patterns, distinct mosaic tiles, specific brushstrokes).
2. **Content Preservation**: The underlying subject matter and composition of the original image should remain recognizable, even if abstracted by the style. 
3. **Uniformity**: Is the style applied cohesively across the image? Sometimes models only apply the style to the background or only to the subject. A good style transfer usually affects the entire image cohesively unless specified otherwise.
4. **Avoid Generic Filters**: Penalize images that simply apply a generic color tint or basic blur instead of genuinely mimicking the requested artistic style.
