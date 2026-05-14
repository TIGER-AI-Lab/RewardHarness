---
description: Guidance on evaluating prompts that reference specific artists, styles,
  or cultural entities.
name: world-knowledge-and-style-awareness
type: skill
---

# World Knowledge and Style Awareness

Prompts often ask for a specific artist's style or a cultural reference (e.g., "inspired by an oversized Claes Oldenburg sculpture").

**Failure Mode:**
Penalizing an image because you do not recognize the artist's specific motifs. For example, Claes Oldenburg is famous for creating giant sculptures of everyday objects (like burgers, spoons, and shuttlecocks). If you assume his work is just "abstract orange sculptures" and penalize an image of a giant burger, you will make an incorrect judgment.

**Guidance:**
1. **Identify Entities:** Pay close attention to named entities, artists, or locations (e.g., "New York subway").
2. **Verify Characteristics:** If an image contains specific elements (like a giant burger for Oldenburg, or specific NYC subway signs), recognize these as strong instruction-following signals.
3. **Avoid Geographic Hallucinations:** If a prompt asks for New York, do not prefer an image that clearly says "Blackfriars" (a London station) just because it looks like a realistic subway.
