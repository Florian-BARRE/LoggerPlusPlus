# ====== Code Summary ======
# Shared pytest fixtures: a loguru sink-capture helper that adds a temporary sink,
# collects formatted records, and always removes the sink afterwards. No sink is
# ever configured at import time — each test opts in explicitly.

from __future__ import annotations

from typing import List

import pytest
from loguru import logger


class LogCapture:
    """Collects loguru output through temporary sinks and cleans them up."""

    def __init__(self) -> None:
        """Initialize an empty buffer and sink-id registry."""
        self.buf: List[object] = []
        self._ids: List[int] = []

    def append(self, message: object) -> None:
        """Raw sink callable: store one formatted record."""
        self.buf.append(message)

    def add(self, fmt: str = "{message}", level: str = "DEBUG") -> "LogCapture":
        """Register a temporary loguru sink writing into the buffer."""
        self._ids.append(logger.add(self.append, format=fmt, level=level))
        return self

    def track(self, sink_id: int) -> None:
        """Track a sink id created elsewhere (e.g. loggerplusplus.add) for teardown."""
        self._ids.append(sink_id)

    @property
    def text(self) -> str:
        """All captured records joined into a single string."""
        return "".join(str(m) for m in self.buf)

    def cleanup(self) -> None:
        """Remove every sink this capture registered."""
        for sink_id in self._ids:
            logger.remove(sink_id)


@pytest.fixture
def cap() -> "LogCapture":
    """Yield a LogCapture and guarantee its sinks are removed after the test."""
    capture = LogCapture()
    try:
        yield capture
    finally:
        capture.cleanup()
