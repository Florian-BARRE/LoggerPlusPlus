# ====== Code Summary ======
# Thread-safe registry for tracking maximum observed field widths to support
# "auto" width alignment in log formatting. Widths are measured in terminal cells
# (visual width) so CJK/wide glyphs align correctly. Exposes public helpers to
# pre-register identifiers, bound growth, reset, and introspect the widths.

from __future__ import annotations

import threading
from typing import Any, Dict, Final, Optional

from .width import sanitize, visual_width

__all__: list[str] = [
    "register_identifier",
    "reset_widths",
    "observed_widths",
    "set_max_auto_width",
]


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
    Stores the max observed visual width per field spec. Used when width='auto'.

    Why process-global and monotonic (never shrinks): loguru formats each record
    independently with no cross-record memory, so the only way to keep a column aligned
    is to remember the widest value seen so far for the whole process and pad every later
    (possibly shorter) value up to it. Shrinking would make columns jitter line to line.
    An optional global cap (`max_auto_width`) bounds growth so a single abnormally long
    value cannot widen a column forever.
    """

    def __init__(self) -> None:
        """
        Initialize the auto-width registry with a re-entrant lock and state.
        """
        # 1. Create synchronization primitive (records are formatted from many threads)
        self._lock: threading.RLock = threading.RLock()
        # 2. Initialize storage for maximum widths per canonical field spec
        self._max_seen: Dict[str, int] = {}
        # 3. Optional global cap on auto widths (None = unbounded)
        self._max_width: Optional[int] = None

    def observe(self, field_spec: str, value: Any) -> None:
        """
        Observe a value for the given field spec and update the maximum width.

        Args:
            field_spec (str): The logical field specifier (e.g., "extra[identifier]").
            value (Any): The observed value; measured by visual (terminal-cell) width.
        """
        # 1. Normalize value to string, measure its visual width, canonicalize the key
        s: str = "" if value is None else str(value)
        seen: int = visual_width(s)
        key: str = _canonical(field_spec)

        # 2. Acquire lock and update maximum if the new value is wider
        with self._lock:
            if seen > self._max_seen.get(key, 0):
                self._max_seen[key] = seen

    def width(self, field_spec: str) -> int:
        """
        Get the current width for a field spec: max observed, capped, floored at 1.

        Args:
            field_spec (str): The field specifier to query.

        Returns:
            int: The effective auto width (>= 1).
        """
        # 1. Read the observed maximum and the optional cap under the lock
        key: str = _canonical(field_spec)
        with self._lock:
            observed = self._max_seen.get(key, 1)
            cap = self._max_width
        # 2. Apply the global cap, then the floor of 1
        if cap is not None:
            observed = min(observed, cap)
        return max(1, observed)

    def observe_and_width(self, field_spec: str, value: Any) -> int:
        """
        Atomically record `value`'s width and return the effective (capped) width.

        Observing and reading back the maximum under a SINGLE lock hold guarantees the
        just-seen value is included in the returned width. Otherwise a concurrent
        `reset()` landing between a separate observe() and width() could drop the width
        to its floor of 1 and hard-cut the record currently being formatted.

        Args:
            field_spec (str): The logical field specifier.
            value (Any): The value being rendered (already sanitized by the caller).

        Returns:
            int: The effective auto width for `value` (>= 1), never below its own width.
        """
        # 1. Measure outside the lock (pure), then update+read the bucket atomically
        s: str = "" if value is None else str(value)
        seen: int = visual_width(s)
        key: str = _canonical(field_spec)
        with self._lock:
            cur = self._max_seen.get(key, 0)
            if seen > cur:
                cur = seen
                self._max_seen[key] = cur
            cap = self._max_width
        # 2. Apply the global cap, then the floor of 1
        if cap is not None:
            cur = min(cur, cap)
        return max(1, cur)

    def preset(self, field_spec: str, value: str) -> None:
        """
        Pre-set (seed) the maximum width using an initial observed value.

        Args:
            field_spec (str): The field specifier to seed.
            value (str): The initial value used to establish width.
        """
        # 1. Delegate to observe to apply standard (canonicalized, visual) width logic
        self.observe(field_spec, value)

    def reset(self) -> None:
        """Forget all observed widths (widths will re-grow from the next record)."""
        with self._lock:
            self._max_seen.clear()

    def snapshot(self) -> Dict[str, int]:
        """Return a copy of the current per-field observed widths."""
        with self._lock:
            return dict(self._max_seen)

    def set_max_width(self, max_width: Optional[int]) -> None:
        """Set (or clear, with None) the global cap on auto widths."""
        if max_width is not None and max_width < 1:
            raise ValueError("max_auto_width must be >= 1 or None")
        with self._lock:
            self._max_width = max_width


_AUTO: Final[_AutoWidthRegistry] = _AutoWidthRegistry()
_IDENTIFIER_SPEC: Final[str] = "extra[identifier]"


def register_identifier(identifier: str) -> None:
    """
    Pre-register an identifier length so alignment is correct from the first line.

    Args:
        identifier (str): The identifier to seed into the auto-width registry.
    """
    # 1. Sanitize (match the render path) and fall back to a placeholder when empty
    seed: str = sanitize(identifier) or "-"
    # 2. Seed the auto-width registry for identifiers (canonicalized to the bare key)
    _AUTO.preset(_IDENTIFIER_SPEC, seed)


def reset_widths() -> None:
    """
    Reset all observed auto widths.

    Useful in long-running processes (to release a width widened by a one-off huge value)
    and in tests (to isolate alignment assertions from earlier records).
    """
    _AUTO.reset()


def observed_widths() -> Dict[str, int]:
    """
    Return a snapshot of the currently observed auto widths, keyed by canonical field.

    Returns:
        dict[str, int]: A copy of field -> max observed visual width.
    """
    return _AUTO.snapshot()


def set_max_auto_width(max_width: Optional[int]) -> None:
    """
    Bound how wide an `auto` column may grow, globally.

    Args:
        max_width (int | None): Maximum cells for any auto field, or None to remove the cap.
    """
    _AUTO.set_max_width(max_width)
