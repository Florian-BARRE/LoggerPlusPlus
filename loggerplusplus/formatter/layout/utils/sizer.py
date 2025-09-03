# ====== Code Summary ======
# This module defines `GlobalFieldSizer`, a utility for dynamically tracking
# maximum observed field widths across log tokens. It supports configurable
# sampling to reduce overhead during logging.

from __future__ import annotations

# ====== Internal Project Imports ======
from ..log_token import LogToken


class GlobalFieldSizer:
    """
    Tracks and updates the maximum observed field widths for log tokens.

    Attributes:
        _max_by_token (dict[LogToken, int]): Cached maximum widths observed per token.
        _sample_period (int): Frequency of updates; higher values reduce overhead.
        _counter (int): Global counter to control sampling.

    Notes:
        - Not thread-safe in its current implementation (no locking).
        - Sample period can be tuned to balance accuracy and performance.
    """

    _max_by_token: dict[LogToken, int] = {}
    _sample_period: int = 1
    _counter: int = 0

    @classmethod
    def set_sample_period(cls, n: int) -> None:
        """
        Configure how often width observations update the cache.

        Args:
            n (int): The sampling period (minimum 1).
        """
        cls._sample_period = max(1, int(n))

    @classmethod
    def observe(cls, tok: LogToken, length: int) -> int:
        """
        Observe a new field width for the given token.

        Args:
            tok (LogToken): The token whose width is being tracked.
            length (int): The observed width.

        Returns:
            int: The maximum width observed so far (may be unchanged).
        """
        # 1. Increment the counter and check if this sample should be processed
        cls._counter += 1
        if cls._counter % cls._sample_period != 0:
            return cls._max_by_token.get(tok, length)

        # 2. Get the current maximum width and update if necessary
        cur: int = cls._max_by_token.get(tok, 0)
        if length > cur:
            cls._max_by_token[tok] = length
            return length

        # 3. Return current maximum (or fallback to the observed length if no record)
        return cur or length
