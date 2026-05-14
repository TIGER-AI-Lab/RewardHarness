import pytest
import json
import os
import shutil
from unittest.mock import MagicMock, patch

@pytest.fixture
def tmp_library(tmp_path):
    """Create a temporary library directory structure."""
    lib_dir = tmp_path / "library"
    lib_dir.mkdir()
    (lib_dir / "skills").mkdir()
    (lib_dir / "tools").mkdir()
    registry_path = lib_dir / "registry.json"
    registry_path.write_text("{}")
    return lib_dir

@pytest.fixture
def mock_vllm_client():
    """Mock OpenAI client for vLLM API calls."""
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = json.dumps({
        "preference": "A",
        "score_A_instruction": 4, "score_A_quality": 3,
        "score_B_instruction": 2, "score_B_quality": 2,
        "reasoning": "A is better"
    })
    client.chat.completions.create.return_value = response
    return client

@pytest.fixture
def mock_gemini_call():
    """Mock call_gemini function for Gemini API calls."""
    with patch("src.gemini_client.call_gemini") as mock_fn:
        mock_fn.return_value = json.dumps({"skills": [], "tools": []})
        yield mock_fn

@pytest.fixture
def sample_skill_md():
    """Sample SKILL.md content for testing."""
    return '''---
name: color-consistency
type: skill
description: Evaluate color consistency between source and edited images
---

## Skill: Color Consistency

Check that colors in the edited region are consistent with the surrounding context.

### Scoring Guide
- 4: Perfect color harmony
- 3: Minor color shifts
- 2: Noticeable color inconsistency
- 1: Severe color mismatch
'''

@pytest.fixture
def sample_tool_md():
    """Sample tool SKILL.md content for testing."""
    return '''---
name: tool-ocr
type: tool
description: Extract text from images for verification
input_schema:
  images: list[base64_str]
  query: str
output_schema:
  text: str
  confidence: float
system_prompt: |
  You are a precise OCR tool. Extract ALL visible text from the provided image(s).
  Return JSON only: {"text": "<extracted text>", "confidence": 0.0-1.0}
---

## Tool: OCR Text Extraction

Reads and returns all visible text from an image.

## Call format
<tool>{"name": "tool-ocr", "images": ["<base64>"], "query": "read all text"}</tool>
'''
