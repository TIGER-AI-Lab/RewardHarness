---
description: Compare a source image and edited images to identify differences, check
  if instructions were followed, and assess visual quality.
input_schema:
  images: list[base64_str]
  query: str
name: compare_images
output_schema:
  comparison_analysis: str
system_prompt: You are an expert image analyst. You will be provided with a source
  image and one or two edited images. Your task is to compare them based on a specific
  query. Identify what has been added
type: tool
---

Use this tool to compare the source image with the edited images. Pass the base64 strings of the images in the `images` list (e.g., `[source_img, edited_a, edited_b]`). Use the `query` to ask specific questions about the edits, such as 'Did the text "begging" get added correctly in both images?', 'Which image better preserves the background?', or 'Are there any visual artifacts in either image?'
