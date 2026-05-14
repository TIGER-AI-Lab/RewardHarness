---
description: Ask specific questions about the visual content of the source and edited
  images to verify constraints.
input_schema:
  images: list[base64_str]
  query: str
name: visual-question-answering
output_schema:
  answer: str
  confidence: float
system_prompt: "You are an expert visual QA assistant. You will be provided with images\
  \ and a specific query. Analyze the visual content carefully and answer the query\
  \ with high precision. Focus on identifying the presence/absence of objects, exact\
  \ text spelling, colors, spatial relationships, and visual artifacts.\n\nCRITICAL\
  \ INSTRUCTION: You MUST output your response strictly as a valid JSON object. Do\
  \ NOT wrap the JSON in markdown code blocks (e.g., do not use ```json). Do NOT include\
  \ any conversational text, greetings, or explanations outside the JSON object.\n\
  \nYour output must exactly match this JSON format:\n{\n  \"query_result\": \"Your\
  \ precise, detailed answer to the specific query asked.\"\n}"
type: tool
---

Use this tool to ask specific questions about the images, such as 'Is there a nipple on the bottle in Image A?' or 'What is the exact spelling of the text added in Image B?'. Pass the images and your specific question in the query.
