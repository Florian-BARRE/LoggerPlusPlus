# ====== Code Summary ======
# This module defines the `TimeFormatter` class, a high-performance time
# formatting utility optimized for logging. It caches formatted seconds to
# reduce repeated computations and supports optional microsecond (%f) handling.

# ====== Standard Library Imports ======
from __future__ import annotations
import time


class TimeFormatter:
    """
    Fast time formatter with cached seconds and optional microsecond (`%f`) handling.

    Attributes:
        fmt (str): The time format string (e.g., "%H:%M:%S.%f").
        _last_sec (int | None): Last formatted second value for caching.
        _cached_prefix (str): Cached prefix string up to the second.
        _has_us (bool): Whether the format string includes microseconds.
    """

    def __init__(self, fmt: str = "%H:%M:%S.%f") -> None:
        """
        Initialize the time formatter.

        Args:
            fmt (str): Format string compatible with `time.strftime`, with optional `%f`
                placeholder for microseconds.
        """
        self.fmt = fmt
        self._last_sec: int | None = None
        self._cached_prefix: str = ""
        self._has_us: bool = "%f" in fmt

    def format(self, created: float) -> str:
        """
        Format a timestamp into a string according to the cached format.

        Args:
            created (float): Timestamp (seconds since epoch, may include fractions).

        Returns:
            str: Formatted time string.
        """
        # 1. Separate seconds and microseconds
        sec = int(created)
        micros = int((created - sec) * 1_000_000) if self._has_us else 0

        # 2. Update cached prefix if second has changed
        if self._last_sec != sec:
            lt = time.localtime(sec)
            if self._has_us:
                base_fmt = self.fmt.replace("%f", "{US}")
                self._cached_prefix = time.strftime(base_fmt, lt)
            else:
                self._cached_prefix = time.strftime(self.fmt, lt)
            self._last_sec = sec

        # 3. Return formatted string (inject microseconds if required)
        if not self._has_us:
            return self._cached_prefix
        return self._cached_prefix.replace("{US}", f"{micros:06d}")
