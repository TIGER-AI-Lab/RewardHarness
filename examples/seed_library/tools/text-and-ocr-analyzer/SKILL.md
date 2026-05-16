---
name: text-and-ocr-analyzer
type: tool
description: Extracts and analyzes text within images to verify spelling, placement, and clarity.
system_prompt: |
  You are an expert OCR and text analysis AI. Extract all visible text from each image provided. For each piece of text, return:
    - the exact characters (preserve case and punctuation)
    - whether the spelling is correct for natural English (or the language of the prompt)
    - approximate placement on the image (top/middle/bottom × left/center/right)
    - any obvious rendering issues (blurry, partially occluded, distorted)
  Be conservative: if you cannot read a character with high confidence, mark it as `?`.
input_schema:
  images: list[base64_str]
  query: str
output_schema:
  image_1_text: str
  image_1_spelling_correct: bool
  image_1_placement: str
  image_2_text: str
  image_2_spelling_correct: bool
  image_2_placement: str
---

# text-and-ocr-analyzer

## When to use

Whenever the prompt asks to **add, modify, or remove text** on an object (signs, labels, captions, t-shirts, posters, license plates, etc.). Many editing models hallucinate plausible-looking but misspelled text — holistic visual evaluation routinely misses this.

## Example query

```text
What text is on the storefront sign in each image? Is it spelled exactly as "Sale"?
```

## Reading the output

Treat a `False` in `image_*_spelling_correct` as strong evidence of instruction-following failure (drop the candidate's instruction-following score by at least 1 point). Treat mismatched `placement` from the prompt's request as a separate, smaller deduction.

## Cost

This tool runs one extra VLM call per evaluation, so don't invoke it unless the prompt explicitly contains text-editing intent.
