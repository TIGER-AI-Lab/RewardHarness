""" API client for RewardHarness orchestration layer."""
import os
import logging

logger = logging.getLogger(__name__)

_client = None


def get_client():
    """Initialize a VertexAI-backed Gemini client.

    Requires GOOGLE_APPLICATION_CREDENTIALS, GEMINI_PROJECT, and GEMINI_LOCATION
    environment variables to be set; see README for setup.
    """
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(
            vertexai=True,
            project=os.environ["GEMINI_PROJECT"],
            location=os.environ.get("GEMINI_LOCATION", "global"),
        )
    return _client


def call_gemini(
    user_message: str,
    model: str = "gemini-3.1-pro-preview",
    system: str = "",
    max_tokens: int = 8192,
    temperature: float = 0,
    response_mime_type: str = None,
) -> str:
    """Single-turn text call to Gemini. No images needed for orch layer."""
    from google.genai import types

    client = get_client()
    response = client.models.generate_content(
        model=model,
        contents=[user_message],
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system or None,
            response_mime_type=response_mime_type,
        ),
    )
    text = ""
    try:
        text = response.text or ""
    except (ValueError, AttributeError):
        for candidate in (response.candidates or []):
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        text += part.text
    if not text.strip():
        raise ValueError(f"Empty response from {model}")
    return text
