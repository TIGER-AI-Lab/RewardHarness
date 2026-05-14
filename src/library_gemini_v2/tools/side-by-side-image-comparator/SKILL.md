---
description: Compares two images side-by-side to definitively determine which image
  contains specific objects, text, or features, preventing feature-swapping.
input_schema:
  images: list[base64_str]
  query: str
name: side-by-side-image-comparator
output_schema:
  differences_summary: str
  image_A_findings: str
  image_B_findings: str
system_prompt: 'You are a precise image comparison assistant. You will receive two
  images: Image A (first) and Image B (second). Your task is to definitively determine
  which image contains specific features, objects, or text requested in the query.
  CRITICAL: Do not mix up the images. Analyze Image A independently, then Image B
  independently. Return a JSON object with: {"image_a_contains_feature": boolean,
  "image_b_contains_feature": boolean, "image_a_description": "brief description of
  the relevant area in A", "image_b_description": "brief description of the relevant
  area in B", "conclusion": "A, B, Both, or Neither"}'
type: tool
---

Use this tool when you need to verify which image contains a specific feature, text, or object to avoid mixing them up.

Example call:
```json
{
  "name": "side-by-side-image-comparator",
  "images": ["<image_A_base64>", "<image_B_base64>"],
  "query": "Which image has the text 'Newerg Yyrk' and which has 'NORRAGE'? Does either image have a nipple on the bottle?"
}
```
