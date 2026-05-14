---
description: Extracts and verifies text rendered in images to accurately evaluate
  text-addition prompts.
input_schema:
  images: list[base64_str]
  query: str
name: text-and-ocr-analyzer
output_schema:
  placement_and_integration: str
  spelling_is_correct: bool
  text_found: str
system_prompt: You are an expert OCR and text analysis tool. Given the images, answer
  the query about the text present in them. Be extremely precise about spelling, capitalization,
  and location of the text. If the text is misspelled or missing, state so clearly.
type: tool
---

# Text and OCR Analyzer

Use this tool whenever a prompt asks to add, modify, or remove specific text (e.g., "Add the letters 'CBS'"). 

**When to use:**
- The prompt contains quotes indicating text to render.
- You need to verify exact spelling, typos, or text placement.

**Example Call:**
```json
{
  "images": ["<image_base64>"],
  "query": "Does the image contain the text 'CBS' on the surfboard?"
}
```
