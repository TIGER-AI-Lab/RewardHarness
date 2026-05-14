---
description: Detects, counts, and locates specific objects in the image, useful for
  instructions targeting a specific instance (e.g., 'the 4th surfboard').
input_schema:
  images: list[base64_str]
  query: str
name: object-locator-and-counter
output_schema:
  count: int
  locations: list[str]
  target_instance_details: str
system_prompt: 'You are an expert object detection and counting assistant. You will
  receive an image and a query asking to locate specific objects (e.g., ''surfboards'').
  Return a JSON object with: {"total_count": integer, "objects": [{"index": integer
  (1 for leftmost/topmost), "description": "brief visual description", "location":
  "spatial location (e.g., far left, center right)"}]}. This helps the user identify
  exactly which object corresponds to an ordinal like ''the 4th item''.'
type: tool
---

# Object Locator and Counter Tool

Use this tool when the prompt requires modifying a specific instance of an object among many (e.g., "the 4th surfboard", "the second person from the left").

**How to use:**
Pass the image and a query like: "Count the surfboards from left to right. Identify the 4th surfboard and describe any text on its black band."
The tool will return the total count, the locations of each, and the specific details of the target instance, helping you verify if the edit was applied to the correct object.
