---
description: Mandates the use of the text-and-ocr-analyzer tool for any text-related
  prompts.
name: mandatory-ocr-for-text
type: skill
---

# Mandatory OCR Tool Usage

When a prompt requires adding, modifying, or verifying text (e.g., "Add the letters 'CBS'", "Add the word 'begging'"), you **MUST** use the `text-and-ocr-analyzer` tool.

**Why?**
Vision-Language Models frequently hallucinate text rendering. You might "see" the correct text when it is misspelled, or misread correct text as random numbers (e.g., misreading "CBS" as "88").

**Action:**
Always call the `text-and-ocr-analyzer` tool to get an objective reading of the text in both images before writing your reasoning or assigning scores.
