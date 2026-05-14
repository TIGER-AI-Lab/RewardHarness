---
description: Ensures strict adherence to requested concepts, rejecting semantic near-misses
  (e.g., classroom vs cafeteria).
name: strict-semantic-and-conceptual-alignment
type: skill
---

# Strict Semantic and Conceptual Alignment

Edits must strictly align with the requested concepts. Semantic near-misses are failures.

## Guidelines
1. **Reject Near-Misses**: If the prompt asks for a 'cafeteria', an image showing a 'classroom with desks and a chalkboard' is a FAILURE. A classroom is not a cafeteria.
2. **Avoid Logical Contradictions**: Do not write contradictory reasoning such as 'Image A changes the background to a classroom... which maintains the context of a cafeteria.' If the concepts are distinct, treat them as distinct.
3. **Read All Details**: Ensure every part of the prompt is addressed. If a specific setting is requested, the visual hallmarks of THAT specific setting must be present, not just a generic or related setting.
