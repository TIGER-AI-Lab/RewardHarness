---
description: Requires explicitly defining specific artists, styles, or entities and
  their visual hallmarks before evaluating.
name: entity-definition-activation
type: skill
---

# Entity Definition Activation

Before evaluating an image based on a specific entity, artist, or style, you MUST explicitly define their visual hallmarks.

1. **Define Before Judging**: State what the entity looks like. For example, 'Claes Oldenburg is known for oversized pop-art sculptures of everyday objects (like burgers, spoons, etc.).'
2. **Avoid Mischaracterization**: Do not guess or apply generic labels. Oldenburg is NOT 'abstract'. If an image shows an abstract sculpture, it fails the Oldenburg prompt. If it shows a giant burger, it succeeds.
3. **Match Hallmarks to Image**: Compare the image's elements directly to your defined hallmarks.
