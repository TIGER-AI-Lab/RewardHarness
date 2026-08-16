"""Transport protocols for dependency-injected model clients."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol


class TextModelClient(Protocol):
    def complete(
        self,
        user_message: str,
        *,
        model: str,
        system: str = "",
        max_tokens: int = 8192,
        temperature: float = 0,
        response_mime_type: str | None = None,
    ) -> str: ...


class ChatModelClient(Protocol):
    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        model: str,
        max_tokens: int,
    ) -> str: ...
