---
description: Guidelines for evaluating object replacements and modifications.
name: evaluating-object-replacements
type: skill
---

# Evaluating Object Replacements
When a prompt asks to change one object into another (e.g., "Wii-remote to a clear plastic bottle with a nipple"):
1. **Constraint Satisfaction**: Check EVERY part of the instruction. If it asks for a "clear plastic bottle" AND "with a nipple", both must be present. Missing a detail is a partial failure.
2. **Exclusivity**: Did the edit affect surrounding areas? For example, if changing a man's glasses to snow goggles, did the model accidentally distort the person next to him? Unintended changes lower the score.
3. **Integration**: Does the new object fit naturally into the scene (lighting, shadows, perspective)?
