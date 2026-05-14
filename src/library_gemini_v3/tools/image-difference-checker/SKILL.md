---
description: Compare a source image and an edited image to list all additions, removals,
  and modifications.
input_schema:
  images: list[base64_str]
  query: str
name: image-difference-checker
output_schema:
  artifacts: list[str]
  intended_edits: list[str]
  unintended_edits: list[str]
system_prompt: "You are an expert image comparison tool. Given a source image and\
  \ an edited image, meticulously list every difference (additions, removals, and\
  \ modifications).\n\nYou MUST output ONLY valid, raw JSON. \n\nCRITICAL INSTRUCTIONS\
  \ FOR JSON OUTPUT:\n"
type: tool
---

Use this tool to compare the source image with an edited image. It will help you identify if the requested changes were made, if any unintended changes occurred, and if there are visual artifacts. Pass the source image and one edited image at a time.
