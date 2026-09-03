# ====== Code Summary ======
# Thread-safe registry for tracking maximum observed field widths to support
# "auto" width alignment in log formatting. Exposes a helper to pre-register
# identifier lengths for improved early alignment.

from __future__ import annotations

import threading
from typing import Any, Final

__all__: list[str] = ["register_identifier"]


def _canonical(field_spec: str) -> str:
    """
    Collapse the two spellings of a field to one registry key.

    A field can be written either bare (`identifier`) or wrapped (`extra[identifier]`);
    both refer to the same logical column, so they MUST share one width bucket. Without
    this, `register_identifier()` (which seeds `extra[identifier]`) and the shipped formats
    (which use the bare `{identifier:...}` token) would track two independent widths and the
    early-alignment guarantee would silently do nothing.

    Args:
        field_spec (str): A field spec such as "identifier", "extra[identifier]", "level.name".

    Returns:
        str: The inner key for an `extra[...]` spec, otherwise the spec unchanged.
    """
    if field_spec.startswith("extra[") and field_spec.endswith("]"):
        return field_spec[6:-1]
    return field_spec


class _AutoWidthRegistry:
    """
    Stores the max observed length per field spec. Used when width='auto'.

    Why process-global and monotonic (never shrinks): loguru formats each record
    independently with no cross-record memory, so the only way to keep a column aligned
    is to remember the widest value seen so far for the whole process and pad every later
    (possibly shorter) value up to it. Shrinking would make columns jitter line to line.
    """

    def __init__(self) -> None:
        """
        Initialize the auto-width registry with a re-entrant lock and state.
        """
        # 1. Create synchronization primitive (records are formatted from many threads)
        self._lock: threading.RLock = threading.RLock()
        # 2. Initialize storage for maximum lengths per canonical field spec
        self._max_seen: dict[str, int] = {}

    def observe(self, field_spec: str, value: Any) -> None:
        """
        Observe a value for the given field spec and update the maximum width.

        Args:
            field_spec (str): The logical field specifier (e.g., "extra[identifier]").
            value (Any): The observed value; converted to string for width calculation.
        """
        # 1. Normalize value to string and the spec to its canonical bucket key
        s: str = "" if value is None else str(value)
        key: str = _canonical(field_spec)

        # 2. Acquire lock and update maximum if the new value is longer
        with self._lock:
            cur: int = self._max_seen.get(key, 0)
            if len(s) > cur:
                self._max_seen[key] = len(s)

    def width(self, field_spec: str) -> int:
        """
        Get the current maximum width for a field spec, with a minimum of 1.

        Args:
            field_spec (str): The field specifier to query.

        Returns:
            int: The maximum observed width, at least 1.
        """
        # 1. Acquire lock for thread-safe read of the canonical bucket
        key: str = _canonical(field_spec)
        with self._lock:
            # 2. Return stored width or fallback to 1
            return max(1, self._max_seen.get(key, 1))

    def preset(self, field_spec: str, value: str) -> None:
        """
        Pre-set (seed) the maximum width using an initial observed value.

        Args:
            field_spec (str): The field specifier to seed.
            value (str): The initial value used to establish width.
        """
        # 1. Delegate to observe to apply standard (canonicalized) width logic
        self.observe(field_spec, value)


_AUTO: Final[_AutoWidthRegistry] = _AutoWidthRegistry()
_IDENTIFIER_SPEC: Final[str] = "extra[identifier]"


def register_identifier(identifier: str) -> None:
    """Pre-register an identifier length (improves early alignment)."""
    # 1. Choose a non-empty placeholder when identifier is falsy
    seed: str = identifier or "-"
    # 2. Seed the auto-width registry for identifiers (canonicalized to the bare key)
    _AUTO.preset(_IDENTIFIER_SPEC, seed)
