"""Vertex AI Gemini client for the RewardHarness orchestration layer.

The Orchestrator (Router + ChainAnalyzer + Evolver) calls Gemini once per
operation: skill/tool selection at inference time, chain analysis at
evolution time. The Sub-Agent does NOT go through this client — it uses an
OpenAI-compatible vLLM endpoint (see src/sub_agent.py).

Usage:
    from src.gemini_client import call_gemini

    text = call_gemini(
        "Pick the 3 most relevant skills for this prompt: ...",
        model="gemini-3.1-pro-preview",
        system="You are a skill router.",
        response_mime_type="application/json",
    )

Environment (required; see .env.example):
    GOOGLE_APPLICATION_CREDENTIALS — path to a Vertex AI service-account JSON
    GEMINI_PROJECT                 — GCP project id with Vertex AI enabled
    GEMINI_LOCATION                — region (default: "global")
"""
import os
import logging

logger = logging.getLogger(__name__)

_client = None


def get_client():
    """Lazy-construct a singleton VertexAI Gemini client.

    Raises:
        KeyError: if GEMINI_PROJECT is not set.
        google.auth.exceptions.DefaultCredentialsError: if
            GOOGLE_APPLICATION_CREDENTIALS is missing or invalid.
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
    """Single-turn text call to Gemini.

    The orchestration layer never needs images — those go to the Sub-Agent.

    Args:
        user_message: the prompt body.
        model: Gemini model id (default: 3.1-pro-preview; do NOT downgrade to 2.5).
        system: optional system instruction.
        max_tokens: cap on `max_output_tokens`.
        temperature: 0 for deterministic routing / analysis.
        response_mime_type: pass "application/json" when you parse the
            output as JSON downstream (recommended for Router + ChainAnalyzer).

    Returns:
        The model's text output. Falls through `response.text` and then walks
        `candidates[*].content.parts` if `.text` raised — needed when the
        model returns a partial response that the SDK's `.text` accessor
        refuses to flatten.

    Raises:
        ValueError: if the model returns no text at all.
    """
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
