# ====== Code Summary ======
# Thread-safe registry for tracking maximum observed field widths to support
# "auto" width alignment in log formatting. Exposes a helper to pre-register
# identifier lengths for improved early alignment.

from __future__ import annotations

# ====== Standard Library Imports ======
import threading

# ====== Third-Party Library Imports ======
# (No third-party imports required)

# ====== Internal Project Imports ======
# (No internal absolute imports required)

# ====== Local Project Imports ======
# (No local relative imports required)

from typing import Any, Final

__all__: list[str] = [
    "_AUTO",
    "_IDENTIFIER_SPEC",
    "register_identifier",
]


class _AutoWidthRegistry:
    """Stores the max observed length per field spec. Used when width='auto'."""

    def __init__(self) -> None:
        """
        Initialize the auto-width registry with a re-entrant lock and state.
        """
        # 1. Create synchronization primitive
        self._lock: threading.RLock = threading.RLock()
        # 2. Initialize storage for maximum lengths per field spec
        self._max_seen: dict[str, int] = {}

    def observe(self, field_spec: str, value: Any) -> None:
        """
        Observe a value for the given field spec and update the maximum width.

        Args:
            field_spec (str): The logical field specifier (e.g., "extra[identifier]").
            value (Any): The observed value; converted to string for width calculation.
        """
        # 1. Normalize value to string
        s: str = "" if value is None else str(value)

        # 2. Acquire lock and update maximum if the new value is longer
        with self._lock:
            cur: int = self._max_seen.get(field_spec, 0)
            if len(s) > cur:
                self._max_seen[field_spec] = len(s)

    def width(self, field_spec: str) -> int:
        """
        Get the current maximum width for a field spec, with a minimum of 1.

        Args:
            field_spec (str): The field specifier to query.

        Returns:
            int: The maximum observed width, at least 1.
        """
        # 1. Acquire lock for thread-safe read
        with self._lock:
            # 2. Return stored width or fallback to 1
            return max(1, self._max_seen.get(field_spec, 1))

    def preset(self, field_spec: str, value: str) -> None:
        """
        Pre-set (seed) the maximum width using an initial observed value.

        Args:
            field_spec (str): The field specifier to seed.
            value (str): The initial value used to establish width.
        """
        # 1. Delegate to observe to apply standard width logic
        self.observe(field_spec, value)


_AUTO: Final[_AutoWidthRegistry] = _AutoWidthRegistry()
_IDENTIFIER_SPEC: Final[str] = "extra[identifier]"


def register_identifier(identifier: str) -> None:
    """Pre-register an identifier length (improves early alignment)."""
    # 1. Choose a non-empty placeholder when identifier is falsy
    seed: str = identifier or "-"
    # 2. Seed the auto-width registry for identifiers
    _AUTO.preset(_IDENTIFIER_SPEC, seed)
