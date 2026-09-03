# ====== Code Summary ======
# Tests for loggerplusplus.testing (audit item A7): the capture() context manager and
# LogCapture buffer used by downstream projects to assert log output.

from __future__ import annotations

from loguru import logger

from loggerplusplus.testing import LogCapture, capture


def test_capture_collects_messages_and_records() -> None:
    """capture() collects rendered messages and the structured records."""
    with capture() as cap:
        logger.bind(identifier="X").info("hello")
    assert isinstance(cap, LogCapture)
    assert "hello" in cap
    assert len(cap) == 1
    assert cap.records[-1]["extra"]["identifier"] == "X"


def test_capture_text_joins_messages() -> None:
    """The `text` property is all rendered messages concatenated."""
    with capture() as cap:
        logger.info("a")
        logger.info("b")
    assert cap.text == "a\nb\n"


def test_capture_removes_its_sink_after_the_block() -> None:
    """Records emitted after the block are not captured."""
    with capture() as cap:
        logger.info("in")
    before = len(cap)
    logger.info("out")
    assert len(cap) == before


def test_capture_respects_level() -> None:
    """A minimum level filters what is captured."""
    with capture(level="WARNING") as cap:
        logger.debug("lo")
        logger.warning("hi")
    assert "hi" in cap
    assert "lo" not in cap
