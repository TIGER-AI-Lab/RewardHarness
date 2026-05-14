---
description: Rules for prioritizing image integrity and penalizing severe artifacts
  or loss of original structure.
name: artifact-and-structure-preservation
type: skill
---

# Artifact and Structure Preservation
A successful image edit must preserve the original image's structure and subject identity (unless instructed to change them) and avoid introducing severe artifacts.

- **Over-editing**: If an edit completely replaces the background or subject in a way that loses the original image's context, penalize it heavily.
- **Artifacts vs. Instruction Following**: If Image B follows the instruction (e.g., rotates an object, adds a crowd) but introduces severe unnatural distortions, missing parts, or obvious AI artifacts, while Image A fails the instruction but remains a clean, natural image, **Image A is often the Ground Truth preference**.
- **Rule of Thumb**: Do not reward an image for following the instruction if it destroys the visual quality, realism, or plausibility of the scene.
