---
name: realism-and-artifact-penalties
type: skill
description: Guidance on penalizing artifacts while allowing conceptual unrealism if requested by the prompt.
---

# Realism and Artifact Penalties

1. **Conceptual unrealism vs. visual artifacts.** If the prompt requests an inherently surreal, dreamlike, cartoon, or otherwise unrealistic scenario (e.g., "make the cat fly", "turn the sky purple", "render in Van Gogh style"), do NOT penalize the image for being conceptually unrealistic. The goal is to follow the prompt.

2. **Penalize visual artifacts.** Only penalize for actual image-processing artifacts, such as:
   - Bad blending or visible seams between edited and original regions
   - Floating objects with missing shadows or contact points
   - Distorted textures, melted faces, extra/missing limbs
   - Color bleeding, halos, or compression noise around edited areas

3. **Prioritize execution quality.** Between two images that both follow the instruction, prefer the one with fewer visual artifacts. Use this skill in combination with `instruction-following-completeness` — an image with perfect realism but partial execution should still lose to one with full execution and minor artifacts.
