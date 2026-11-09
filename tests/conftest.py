# ====== Code Summary ======
# Shared pytest fixtures and helper functions for the loggerplusplus test suite.
#
# Fixtures:
#   cap — LogCapture with automatic sink teardown (via append/add/tracking).
#   custom_cap — list-capture fixture: yields a list of logged strings,
#                removes the loguru sink on teardown. Used by tests that need
#                the raw list (redaction, truncation, min_duration).
#
# Helper functions (import via ``from tests.conftest import _render, _run``):
#   _render(token, record) — one auto-width filter pass, returns the placeholder.
#   _run(fmt, record) — parse + compose + filter, returns the full ``extra`` dict.

from __future__ import annotations

from typing import Any, Dict, List

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


# ── List-capture fixture ────────────────────────────────────────────────────


@pytest.fixture
def custom_cap() -> Any:
    """Capture emitted log messages to a list, then remove the sink."""
    messages: List[str] = []
    sink_id = logger.add(messages.append, level="DEBUG", format="{message}")
    try:
        yield messages
    finally:
        logger.remove(sink_id)


# ── Auto-width filter helpers ───────────────────────────────────────────────


def _run(fmt: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Parse *fmt*, compose the filter, run it against *record*, return *extra*."""
    from loggerplusplus.parser import prepare_auto_format
    from loggerplusplus.runtime import compose_filter

    _new_fmt, mappings = prepare_auto_format(fmt)
    flt = compose_filter(None, mappings)
    flt(record)
    return record.get("extra", {})


def _render(token: str, record: Dict[str, Any]) -> str:
    """Render a single-token format against *record* and return the placeholder."""
    from loggerplusplus.parser import prepare_auto_format
    from loggerplusplus.runtime import compose_filter

    _new_fmt, mappings = prepare_auto_format(token)
    compose_filter(None, mappings)(record)
    return record.get("extra", {}).get("__lp_auto_0__", "")


def _render_value(token: str, value: str) -> str:
    """Render one token for *value* and return the placeholder.

    Thin adapter for tests that pass ``value`` instead of a full ``record`` dict.
    The *value* is placed under key ``"x"`` in ``extra``.
    """
    from loggerplusplus.parser import prepare_auto_format
    from loggerplusplus.runtime import compose_filter

    _new_fmt, mappings = prepare_auto_format(token)
    rec: Dict[str, Any] = {"extra": {"x": value}}
    compose_filter(None, mappings)(rec)
    return rec.get("extra", {}).get("__lp_auto_0__", "")


# ── Decorator test helpers ──────────────────────────────────────────────────


def _frozen_clock(monkeypatch: "pytest.MonkeyPatch", values: List[float]) -> None:
    """Patch time.perf_counter to yield fixed values so a measured duration is

    byte-stable (monkeypatch restores the real clock on teardown)."""
    import time

    it = iter(values)
    monkeypatch.setattr(time, "perf_counter", lambda: next(it))
