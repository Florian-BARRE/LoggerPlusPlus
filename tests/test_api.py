# ====== Code Summary ======
# Coverage for api.add(): the auto-width branch (format string with custom tokens
# wraps the filter via compose_filter) and the plain-format passthrough.

from __future__ import annotations

from loguru import logger

from loggerplusplus import loggerplusplus


def test_add_auto_width_pads_identifier(cap: "object") -> None:
    """A format with an auto-width identifier token pads the value at render time."""
    sink_id = loggerplusplus.add(
        cap.append,
        level="DEBUG",
        format="[{extra[identifier]:<auto}] {message}",
    )
    cap.track(sink_id)

    logger.bind(identifier="SVC").info("up")
    assert "[SVC] up" in cap.text

    logger.bind(identifier="LONGERNAME").info("second")
    # The observed width grew to the longest identifier, so the short one is padded.
    logger.bind(identifier="AB").info("third")
    assert "[AB        ] third" in cap.text


def test_add_plain_format_passthrough(cap: "object") -> None:
    """A plain format with no custom token is forwarded to loguru unchanged."""
    sink_id = loggerplusplus.add(cap.append, level="INFO", format="{message}")
    cap.track(sink_id)
    logger.info("plain")
    assert "plain" in cap.text


def test_add_returns_sink_id(cap: "object") -> None:
    """add() returns an integer sink id usable for removal."""
    sink_id = loggerplusplus.add(cap.append, level="DEBUG", format="{message}")
    cap.track(sink_id)
    assert isinstance(sink_id, int)
