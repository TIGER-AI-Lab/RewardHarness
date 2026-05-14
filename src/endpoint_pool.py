"""Thread-safe round-robin endpoint pool for vLLM servers.

Loads endpoint URLs from a text file (one URL per line).
Provides next() method for round-robin distribution across all endpoints.
Used by both SubAgent (main reasoning) and Library.call_tool (tool calls).
"""

import threading


class EndpointPool:
    def __init__(self, endpoints: list = None, endpoints_file: str = None):
        """Initialize endpoint pool.

        Args:
            endpoints: List of endpoint URLs directly
            endpoints_file: Path to file with one endpoint URL per line
        """
        if endpoints:
            self._endpoints = list(endpoints)
        elif endpoints_file:
            with open(endpoints_file) as f:
                self._endpoints = [
                        line.strip() for line in f
                        if line.strip() and not line.strip().startswith('#')
                    ]
        else:
            raise ValueError("Must provide either endpoints list or endpoints_file path")

        if not self._endpoints:
            raise ValueError("No endpoints provided")

        self._index = 0
        self._lock = threading.Lock()

    def next(self) -> str:
        """Return the next endpoint URL in round-robin order. Thread-safe."""
        with self._lock:
            url = self._endpoints[self._index]
            self._index = (self._index + 1) % len(self._endpoints)
            return url

    @property
    def size(self) -> int:
        """Number of endpoints in the pool."""
        return len(self._endpoints)

    def all(self) -> list:
        """Return all endpoint URLs."""
        return list(self._endpoints)
