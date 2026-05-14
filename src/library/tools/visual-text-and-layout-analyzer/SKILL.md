---
description: Analyzes images for exact text content (OCR), spelling, object counting,
  and spatial relationships (e.g., under, in front of).
input_schema:
  images: list[base64_str]
  query: str
name: visual-text-and-layout-analyzer
output_schema:
  extracted_text: list[str]
  object_counts: dict[str, int]
  spatial_relationships: dict[str, str]
  text_positions: list[str]
system_prompt: 'You are a precise visual analyzer. Given an image and a query, you
  must return a JSON object. For text queries, return the exact text found (including
  misspellings) and its location. For counting, return the exact number of specified
  objects. For spatial queries, describe the exact relationship between the objects
  (e.g., ''A is under B'', ''A is to the left of B''). Output schema: {"text_found":
  ["str"], "object_counts": {"object": "int"}, "spatial_relationships": ["str"]}'
type: tool
---

Call this tool when the prompt involves adding specific text, counting objects (e.g., '4th surfboard'), or spatial positioning (e.g., 'under the bag', 'in front of'). Query example: 'What text is written on the surfboards, and on which surfboard from the left is it located?'
