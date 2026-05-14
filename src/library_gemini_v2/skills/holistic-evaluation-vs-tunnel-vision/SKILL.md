---
description: Prevents tunnel vision on specific requested edits by enforcing holistic
  evaluation, penalizing collateral damage, anatomical distortion, and loss of original
  context.
name: holistic-evaluation-vs-tunnel-vision
type: skill
---

# Holistic Evaluation vs. Tunnel Vision
When evaluating an image, do not get 'tunnel vision' on the specific requested object or edit (e.g., 'bottle with a nipple', 'snow goggles', 'home plate'). You MUST evaluate the image holistically.

## Core Directives:
1. **Assess Collateral Damage**: Did the edit destroy the subject's hands, face, or body? (e.g., adding a bottle but mangling the hand holding it).
2. **Context Preservation**: Did the edit unnecessarily alter the background, lighting, or other objects that were not supposed to change?
3. **Integration Quality**: Is the new object integrated naturally, or does it look like a grotesque, pasted-on artifact?

## Decision Rule:
If Image B perfectly generates the requested object but ruins the subject's anatomy, introduces severe artifacts, or destroys the image context, while Image A generates a slightly less accurate object (or fails the instruction) but preserves the image perfectly, **Image A is often preferred**. Instruction fulfillment does NOT excuse severe degradation of image quality, structure, or realism.
