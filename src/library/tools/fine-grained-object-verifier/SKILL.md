---
description: Verifies the presence, exact attributes, and transformations of specific
  objects (e.g., 'clear plastic bottle with a nipple').
input_schema:
  images: list[base64_str]
  query: str
name: fine-grained-object-verifier
output_schema:
  artifacts_detected: str
  attributes_match: bool
  discrepancies: str
  objects_found: list[str]
system_prompt: 'You are an expert object verifier. Given an image and a query about
  specific object attributes (e.g., ''clear plastic bottle with a nipple'', ''polar
  bears in a savannah''), verify if ALL attributes and contexts are present. Return
  a JSON object detailing exactly what is present and what is missing. Output schema:
  {"primary_object_present": "bool", "attributes_found": ["str"], "attributes_missing":
  ["str"], "background_or_context": "str", "unintended_objects_introduced": ["str"]}'
type: tool
---

Call this tool when the prompt asks for complex object transformations or specific attributes (e.g., 'snow goggles', 'clear plastic bottle with a nipple', 'dark aged metal'). Query example: 'Does the image contain a clear plastic bottle with a nipple? Are there any Wii-remotes left?'
