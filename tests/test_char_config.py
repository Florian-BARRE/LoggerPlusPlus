# ====== Code Summary ======
# Phase 3 characterization (safety-net) tests for the public boundary: the
# auto-width registry controls (register_identifier, reset_widths,
# observed_widths, set_max_auto_width, import_widths) and the one-call setup
# (setup / configure_from_env).
#
# These pin the CURRENT behaviour, right or wrong, so a later refactoring
# ticket can prove it changed nothing. Every golden was captured by running
# the real code and reading the returned value — do NOT edit a golden to make
# a refactor pass; a diff here means observable output changed.
#
# Determinism: the process-global auto-width registry is reset (and any global
# cap cleared) before and after every test, and every sink is removed, so a
# render is byte-stable across runs, machines and test order. Renders use a
# fixed, injected identifier (via logger.bind) and plain (colorize=False)
# formats, so no wall-clock, random or thread-id values appear.

from __future__ import annotations

import re
import sys
from typing import Any, List

import pytest
from loguru import logger

from loggerplusplus import (
    add,
    configure_from_env,
    formats,
    import_widths,
    observed_widths,
    register_identifier,
    reset_widths,
    set_max_auto_width,
    setup,
)
from loggerplusplus import logger as lp
from loggerplusplus.formats import ClassicFormat

# ====== Local Test Helpers ====== #

# A fixed, wide (CJK) identifier: three East-Asian-wide glyphs, 6 visual cells.
_CJK = "漢字語"


@pytest.fixture(autouse=True)
def _clean() -> Any:
    """Isolate the process-global registry and the global sink set per test."""
    logger.remove()
    reset_widths()
    set_max_auto_width(None)
    yield
    logger.remove()
    reset_widths()
    set_max_auto_width(None)


def _render(fmt: str, identifiers: List[str], message: str = "m") -> List[str]:
    """Render one plain auto-width token per bound identifier and return the lines."""
    buf: List[object] = []
    logger.remove()
    add(buf.append, format=fmt, colorize=False)
    for ident in identifiers:
        lp.bind(identifier=ident).info(message)
    return [str(line).rstrip("\n") for line in buf]


# ====== 1. register_identifier -> observed_widths snapshot ====== #


def test_register_identifier_pins_ascii_observed_width() -> None:
    """register_identifier seeds the `identifier` bucket with the max visual width."""
    register_identifier("WorkerService")  # 13 cells
    assert observed_widths() == {"identifier": 13}


def test_register_identifier_pins_cjk_wide_char_width() -> None:
    """A CJK identifier is measured in cells: three wide glyphs observe as 6, not 3."""
    register_identifier(_CJK)  # 3 code points, 6 visual cells
    assert observed_widths() == {"identifier": 6}


def test_register_identifier_keeps_max_of_wide_and_ascii() -> None:
    """Registering a wider ASCII id after a wide one keeps the max (monotonic)."""
    register_identifier(_CJK)  # 6 cells
    register_identifier("WorkerService")  # 13 cells, wider
    assert observed_widths() == {"identifier": 13}


def test_register_identifier_empty_seeds_placeholder() -> None:
    """An empty identifier falls back to the '-' sentinel (1 cell), not 0."""
    register_identifier("")
    assert observed_widths() == {"identifier": 1}


# ====== 2. reset_widths clears the registry ====== #


def test_reset_widths_clears_observed_snapshot() -> None:
    """reset_widths empties the snapshot; a re-register grows from scratch."""
    register_identifier("WorkerService")
    register_identifier(_CJK)
    assert observed_widths() == {"identifier": 13}
    reset_widths()
    assert observed_widths() == {}


# ====== 3. set_max_auto_width bounds a field's width ====== #


def test_set_max_auto_width_caps_rendered_column() -> None:
    """With a cap, a wider observed value is hard-cut to the cap when rendered."""
    set_max_auto_width(4)
    register_identifier("WorkerService")  # 13 cells observed, capped at 4
    # _CJK (6 cells) hard-cuts to 4 cells -> two wide glyphs; 'ab' pads to 4.
    assert _render("{identifier:<auto} -> {message}", [_CJK, "ab"]) == [
        "漢字 -> m",
        "ab   -> m",
    ]


def test_set_max_auto_width_not_applied_to_snapshot() -> None:
    """A cap bounds rendering only: observed_widths() still reports the raw max."""
    set_max_auto_width(4)
    register_identifier("WorkerService")  # 13 cells
    assert observed_widths() == {"identifier": 13}


def test_set_max_auto_width_none_restores_unbounded_render() -> None:
    """Clearing the cap lets a column render at its full observed width again."""
    set_max_auto_width(4)
    set_max_auto_width(None)
    assert _render("{identifier:<auto} -> {message}", ["WorkerService"]) == [
        "WorkerService -> m",
    ]


def test_set_max_auto_width_rejects_below_one() -> None:
    """A cap below 1 is rejected with a ValueError."""
    with pytest.raises(ValueError):
        set_max_auto_width(0)


# ====== 4. import_widths seeds from a snapshot (cross-process path) ====== #


def test_import_widths_seeds_observed_snapshot() -> None:
    """import_widths seeds the registry from a Mapping snapshot (canonical keys)."""
    import_widths({"identifier": 20, "name": 5})
    assert observed_widths() == {"identifier": 20, "name": 5}


def test_import_widths_max_merge_semantics() -> None:
    """import_widths keeps the maximum per field: smaller values do not shrink it."""
    import_widths({"identifier": 20})
    register_identifier("ab")  # 2 < 20: no change
    import_widths({"identifier": 3})  # 3 < 20: no change
    import_widths({"identifier": 30})  # 30 > 20: grows
    assert observed_widths() == {"identifier": 30}


# ====== 5. one-call setup / configure_from_env ====== #


def test_setup_returns_console_id_and_applies_plain_format(cap: Any) -> None:
    """setup(format=<named>) installs one console sink rendering the resolved format."""
    plain = formats.MinimalFormat(colorized=False)
    ids = setup(format=plain, sink=lambda m: None, colorize=False)
    assert set(ids) == {"console"}
    # Capture a full rendered line through the auto-rewriting `add` (the `cap`
    # fixture's own add() is raw loguru and would not resolve the auto token).
    cap.track(add(cap.append, format=str(plain), colorize=False))
    lp.bind(identifier="SETUP").info("console hi")
    assert cap.text == "SETUP -> console hi\n"


def test_configure_from_env_applies_env_vars_to_file_sink(
    monkeypatch: Any, tmp_path: Any
) -> None:
    """LOGGING_LPP_* vars drive the resolved format, level and a plain file sink."""
    logfile = tmp_path / "char.log"
    monkeypatch.setenv("LOGGING_LPP_FORMAT", "MinimalFormat")
    monkeypatch.setenv("LOGGING_LPP_LEVEL", "INFO")
    monkeypatch.setenv("LOGGING_LPP_FILE", str(logfile))
    logger.remove()
    ids = configure_from_env()
    assert set(ids) == {"console", "file"}
    assert ids["console"] != ids["file"]
    # LEVEL=INFO filters the DEBUG record; the file sink renders plain MinimalFormat.
    lp.bind(identifier="ENV").debug("filtered-debug")
    lp.bind(identifier="ENV").info("kept-info")
    logger.remove()
    assert logfile.read_text() == "ENV -> kept-info\n"


def test_configure_from_env_default_has_console_only(
    monkeypatch: Any, cap: Any
) -> None:
    """With only a FORMAT var set, configure_from_env adds one console sink."""
    monkeypatch.setenv("LOGGING_LPP_FORMAT", "MinimalFormat")
    logger.remove()
    ids = configure_from_env()
    assert set(ids) == {"console"}
    # The env-resolved console sink targets sys.stderr; capture a matching plain
    # line through the auto-rewriting `add` on the same resolved format.
    plain = str(formats.MinimalFormat(colorized=False))
    cap.track(add(cap.append, format=plain, colorize=False))
    lp.bind(identifier="ENV2").info("console from env")
    assert cap.text == "ENV2 -> console from env\n"


# ====== 6. real sys.stderr sink, end to end ====== #

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def test_real_stderr_sink_renders_aligned_identifier_column(capfd: Any) -> None:
    """A real `sys.stderr` sink added like a user would renders the aligned column.

    `capfd` (fd-level capture), not `capsys`: loguru keeps the `sys.stderr` object it
    saw at add-time, so only the real fd 2 receives its writes.
    """
    logger.remove()
    sink_id = add(sink=sys.stderr, level="DEBUG", format=ClassicFormat())
    try:
        lp.bind(identifier="LongIdentifier").info("first line")
        lp.bind(identifier="ab").debug("second line")
    finally:
        logger.remove(sink_id)
    lines = _ANSI.sub("", capfd.readouterr().err).splitlines()
    assert len(lines) == 2
    assert "[LongIdentifier]" in lines[0] and lines[0].endswith("first line")
    # The short identifier is centred in the 14-cell column set by the long one.
    assert "[      ab      ]" in lines[1] and lines[1].endswith("second line")
    assert "DEBUG" in lines[1]
