# ====== Code Summary ======
# Regression tests for control-sequence sanitization: a control char in a field must
# not split a log line (log injection) and an ANSI escape must not poison the shared
# auto-width column. Found by adversarial testing of the visual-width engine.

from __future__ import annotations

from typing import Any, List

import pytest

from loggerplusplus import (
    add,
    loggerplusplus,
    observed_widths,
    remove,
    reset_widths,
    set_max_auto_width,
)
from loggerplusplus.width import sanitize


@pytest.fixture(autouse=True)
def _clean_registry() -> Any:
    """Isolate width state around each test."""
    reset_widths()
    set_max_auto_width(None)
    yield
    reset_widths()
    set_max_auto_width(None)


def _capture(identifier: str, message: str, fmt: str) -> List[str]:
    """Log one record through the real enhanced sink and return the emitted lines."""
    lines: List[str] = []
    sink_id = add(sink=lines.append, level="DEBUG", format=fmt, colorize=False)
    try:
        loggerplusplus.bind(identifier=identifier).info(message)
    finally:
        remove(sink_id)
    return lines


# --- width.sanitize unit --------------------------------------------------------------


def test_sanitize_drops_control_characters() -> None:
    """Newline, tab, NUL and ESC are removed."""
    assert sanitize("a\nb\tc\x00d\x1be") == "abcde"


def test_sanitize_strips_ansi_sequences() -> None:
    """ANSI colour sequences are removed, leaving the visible text."""
    assert sanitize("\x1b[31mRED\x1b[0m") == "RED"


def test_sanitize_keeps_normal_and_zero_width_joiners() -> None:
    """Printable text and format joiners (needed by emoji) are preserved."""
    assert sanitize("hello") == "hello"
    assert sanitize("a‍b") == "a‍b"  # ZWJ is category Cf, kept


# --- public path: no log injection ----------------------------------------------------


def test_newline_in_identifier_does_not_split_the_line() -> None:
    """A newline in an identifier must not turn one record into two physical lines."""
    lines = _capture("a\nb", "payload", "[{identifier:<auto}] {message}")
    assert len(lines) == 1
    text = lines[0]
    assert text.count("\n") == 1  # only the trailing record newline
    assert text.rstrip("\n").count("\n") == 0
    assert "[ab]" in text


# --- public path: ANSI does not poison the shared column ------------------------------


def test_ansi_identifier_does_not_poison_auto_width() -> None:
    """An escape-laden identifier widens the column only to its visible width."""
    _capture("\x1b[31mRED\x1b[0m", "x", "[{identifier:<auto}] {message}")
    # "RED" is 3 visible cells; the raw escape bytes must not count.
    assert observed_widths().get("identifier") == 3
