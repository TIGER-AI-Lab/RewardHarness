---
description: Ask specific questions about visual content, style, spatial relationships,
  or differences between images.
input_schema:
  images: list[base64_str]
  query: str
name: visual-question-answering
output_schema:
  answer: str
  details: list[str]
system_prompt: "You are an expert visual analyst. Answer the user's query about the\
  \ provided images accurately and concisely. If comparing images, highlight specific\
  \ visual differences, spatial relationships, over-editing of backgrounds, or stylistic\
  \ elements. Be highly observant of subtle details.\n\nYou MUST output your response\
  \ strictly as a valid, raw JSON object. Do NOT wrap the JSON in markdown code blocks\
  \ (e.g., do not use ```json or ```). Do not include any conversational text before\
  \ or after the JSON.\n\nReturn exactly this JSON structure:\n{\n  \"response\":\
  \ \"Your detailed answer to the user's query\"\n}"
type: tool
---

Use this tool to ask specific questions about the images. You can pass the source image and edited images to compare them. 

Example queries:
- "Compare the background of Image A and Image B to the source image. Did either image change the background unnecessarily?"
- "Counting from the left, which surfboard has the text 'CBS' on it in Image A?"
- "Does the image look like a Claes Oldenburg sculpture? Describe the artistic style."
- "Is the cat's foot placed *under* the bag or *on top* of the bag?"
