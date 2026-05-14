---
description: Strategy for evaluating prompts containing specific artists, cultural
  references, or named entities.
name: world-knowledge-and-entities
type: skill
---

# World Knowledge & Named Entities
Prompts often contain specific cultural references, artists, or locations (e.g., "Claes Oldenburg", "New York subway").

## Strategy:
1. **Identify Entities**: Before looking at the images, identify any proper nouns or specific styles in the prompt.
2. **Recall Characteristics**: Recall the visual hallmarks of that entity. 
   - *Example*: "Claes Oldenburg" is famous for creating massive, oversized sculptures of mundane, everyday objects (like burgers, spoons, shuttlecocks). He does NOT just make generic abstract sculptures.
   - *Example*: "New York subway" has specific visual cues (MTA signs, specific tile patterns, specific train car designs).
3. **Evaluate Based on Specifics, Not Generics**: If Image A contains the specific hallmark (e.g., an oversized burger) and Image B contains a generic interpretation (e.g., a large abstract orange sculpture), Image A is the correct interpretation, even if it looks less like a traditional "sculpture" to a naive observer.
