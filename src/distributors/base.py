"""Distributor Protocol — base interface for all distributors."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Distributor(Protocol):
    def distribute(self, result: Any, agent: Any) -> str:
        """Distribute result. Returns a human-readable status message."""
        ...
