"""Compatibility wrapper for :mod:`rewardharness.evaluation.engine`."""

from src._compat import warn_legacy

warn_legacy(__name__)

from rewardharness.evaluation.engine import (
    BASE_INSTRUCTIONS_NO_TOOLS,
    FALLBACK_ANSWER,
    MAX_TOOL_CALLS,
    SCORE_TEMPLATES_DIR,
    SUBAGENT_MODEL,
    TOOL_INSTRUCTIONS,
    SubAgent,
)

__all__ = [
    "BASE_INSTRUCTIONS_NO_TOOLS",
    "FALLBACK_ANSWER",
    "MAX_TOOL_CALLS",
    "SCORE_TEMPLATES_DIR",
    "SUBAGENT_MODEL",
    "TOOL_INSTRUCTIONS",
    "SubAgent",
]
