---
description: Analyzes images to verify exact settings (e.g., cafeteria vs classroom),
  fine-grained details, and extreme artifacts.
input_schema:
  images: list[base64_str]
  query: str
name: visual-detail-and-setting-analyzer
output_schema:
  artifact_or_corruption: bool
  detail_present: bool
  explanation: str
  setting_description: str
system_prompt: You are an expert visual analyzer. Your task is to analyze images to
  verify exact settings (e.g., cafeteria vs classroom), fine-grained details, and
  extreme artifacts based on the user
type: tool
---

# Visual Detail and Setting Analyzer

Use this tool when you need to verify:
1. **Exact Settings**: To distinguish between similar environments (e.g., 'Is this a cafeteria or a classroom?').
2. **Fine-Grained Details**: To check if a specific small detail requested in the prompt is actually present (e.g., 'Does the clear plastic bottle have a nipple?').
3. **Extreme Artifacts**: To verify if an image is actually a completely black screen or corrupted, preventing hallucinated claims of image failure.

**Example Call**:
```json
<tool>{"name": "visual-detail-and-setting-analyzer", "images": ["<base64_A>", "<base64_B>"], "query": "Is the setting a school cafeteria with dining tables, or a classroom with desks? Does the bottle have a nipple?"}</tool>
```
