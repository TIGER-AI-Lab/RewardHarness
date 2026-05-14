---
description: Extracts and verifies text in the image, checking for exact string matches,
  spelling errors, and legibility.
input_schema:
  images: list[base64_str]
  query: str
name: text-and-spelling-checker
output_schema:
  exact_match: boolean
  extracted_text: list[str]
  legibility_notes: str
  spelling_errors: list[str]
system_prompt: You are an expert OCR and text analysis model. Extract all visible
  text in the provided image(s). Compare the extracted text against the user's query
  to check for exact string matches, spelling errors
type: tool
---

# Text and Spelling Checker
Use this tool whenever the prompt asks to add, modify, or verify text in an image.
- **When to use**: Prompts containing quotes (e.g., Add the word "begging", letters "CBS").
- **Why**: VLMs often overlook subtle typos (e.g., "beging" instead of "begging", "gegging"). This tool explicitly extracts and checks the spelling.
- **Usage**: Pass the image and a query like "Check if the word 'begging' is spelled correctly and where it is located."
