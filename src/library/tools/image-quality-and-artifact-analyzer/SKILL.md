---
description: Analyzes a single edited image for visual artifacts, distortions, blurriness,
  unnatural lighting, and over-editing.
input_schema:
  images: list[base64_str]
  query: str
name: image-quality-and-artifact-analyzer
output_schema:
  flaws: list[str]
  quality_score: int
  blending_quality: str
system_prompt: You are an expert image quality evaluator. Analyze the provided edited
  image (compared to the source) for visual artifacts, distortions, blurriness, unnatural
  lighting, over-editing, and poor blending of edited elements. Specifically check
  how well new objects are integrated into the scene in terms of lighting, shadows,
  and perspective. Return a JSON with keys "flaws" (list of specific issues found),
  "quality_score" (1-4 integer), and "blending_quality" (description of how well edits
  blend with the original).
type: tool
---

# Image Quality and Artifact Analyzer

Use this tool to objectively assess the visual quality of the edited image compared to the source.

**When to use:**
- When you need to assess visual quality objectively before scoring.
- When you suspect the edited image has artifacts, distortions, or unnatural blending.

**Example Call:**
```json
<tool>{"name": "image-quality-and-artifact-analyzer", "images": ["source", "edited"], "query": "Analyze the edited image for any artifacts, distortions, or unnatural lighting introduced by the edit."}</tool>
```
