---
description: Extracts and verifies text from specific regions of images to prevent
  hallucinating text or mixing up Image A and Image B.
input_schema:
  images: list[base64_str]
  query: str
name: text-and-ocr-verifier
output_schema:
  analysis: str
  image_A_text: str
  image_B_text: str
system_prompt: You are a strict OCR and text verification assistant. Your job is to
  extract text from Image A and Image B separately. If asked to find a specific word,
  report exactly what is written in Image A and exactly what is written in Image B,
  including any typos, misspellings, or completely wrong characters. Be extremely
  careful not to swap the results for Image A and Image B. Output your findings clearly
  labeled for 'Image A' and 'Image B'.
type: tool
---

# Text and OCR Verifier

Use this tool when the prompt requires adding, modifying, or verifying specific text in the image.

**When to use:**
- The prompt asks to add a specific word or letters (e.g., "Add the letters 'CBS'").
- You need to verify if a typo was made (e.g., '8' instead of 'CBS', or 'bgciig' instead of 'begging').

**How to use:**
Pass the images and a query like "What text is written on the black band of the 4th surfboard?" The tool will return the exact text found in both images, helping you avoid mixing up Image A and Image B or hallucinating correct spelling.
