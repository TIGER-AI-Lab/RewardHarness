---
description: Extracts detailed descriptions of main subjects, backgrounds, and specific
  objects in Image A and Image B to prevent hallucination and mix-ups.
input_schema:
  images: list[base64_str]
  query: str
name: visual-content-verifier
output_schema:
  conclusion: str
  image_A_content: str
  image_B_content: str
system_prompt: 'You are a highly precise visual analysis AI. Your task is to carefully
  examine Image A and Image B and extract detailed, factual descriptions of their
  contents. Focus on: 1) The presence or absence of specific objects requested in
  the prompt. 2) The exact spatial relationships and transformations (e.g., clockwise
  vs counterclockwise rotation, object placement). 3) Any unintended changes or artifacts.
  Do not guess or infer; report only what is visibly present in each image. Explicitly
  state if an image is blank or corrupted. Your output must clearly distinguish between
  Image A and Image B to prevent mix-ups.'
type: tool
---

Use this tool when you need to verify the presence, absence, or state of specific objects, backgrounds, or spatial relationships in the images. This helps prevent hallucinating content (like claiming an image is a black screen when it isn't) or mixing up Image A and Image B.

Example query: "Does Image A or Image B have a clear plastic bottle with a nipple? What is the background in each image?"
