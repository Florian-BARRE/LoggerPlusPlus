# ====== Code Summary ======
# Tests for the transform/raw keyword plumbing (transform_proxy.py): the keyword works on the
# singleton, on a bound TransformProxy, and on LoggerClass.logger; the transform runs AFTER
# loguru-style substitution; raw mode drops the format prefix; caller attribution stays at the
# user's call site (guards _CALLER_DEPTH); and non-level attributes keep exact loguru semantics.

from __future__ import annotations

import io
from typing import Any, List

from loguru import logger

from loggerplusplus import Banner, LoggerClass, loggerplusplus
from loggerplusplus.decorators import catch as project_catch
from loggerplusplus.transform_proxy import TransformProxy

# --------------------------------------------------------------------------- transform applied


def test_transform_on_singleton_info(cap: Any) -> None:
    """The singleton's `.info` applies the transform to the message."""
    cap.add(fmt="{message}")
    loggerplusplus.info("hello", transform=str.upper)
    assert cap.text == "HELLO\n"


def test_transform_on_bound_logger(cap: Any) -> None:
    """A logger obtained via `.bind` keeps the transform keyword (it is a TransformProxy)."""
    cap.add(fmt="{message}")
    bound = loggerplusplus.bind(identifier="TP_BOUND")
    assert isinstance(bound, TransformProxy)
    bound.info("hello", transform=str.upper)
    assert cap.text == "HELLO\n"


def test_transform_on_logger_class_logger(cap: Any) -> None:
    """`LoggerClass(...).logger` is a TransformProxy and honours the transform keyword."""
    cap.add(fmt="{message}")

    class TP_Service(LoggerClass):
        pass

    svc = TP_Service(identifier="TP_SVC")
    assert isinstance(svc.logger, TransformProxy)
    svc.logger.info("hello", transform=str.upper)
    assert cap.text == "HELLO\n"


def test_transform_runs_after_substitution(cap: Any) -> None:
    """The transform sees the already-substituted string, not the raw template."""
    cap.add(fmt="{message}")
    loggerplusplus.info("{n} items", n=3, transform=str.upper)
    assert cap.text == "3 ITEMS\n"


def test_transform_positional_substitution(cap: Any) -> None:
    """Positional format args are substituted before the transform runs."""
    cap.add(fmt="{message}")
    loggerplusplus.info("{} and {}", "a", "b", transform=str.upper)
    assert cap.text == "A AND B\n"


def test_passthrough_without_transform(cap: Any) -> None:
    """Without transform or raw, the message logs verbatim (fast path)."""
    cap.add(fmt="{message}")
    loggerplusplus.info("plain {v}", v=1)
    assert cap.text == "plain 1\n"


def test_transform_on_log_method(cap: Any) -> None:
    """`.log(level, msg, transform=...)`: the message is the 2nd positional."""
    cap.add(fmt="{level.name} {message}")
    loggerplusplus.log("WARNING", "{who} here", who="me", transform=str.upper)
    assert cap.text == "WARNING ME HERE\n"


# --------------------------------------------------------------------------- raw mode


def test_raw_mode_drops_prefix_and_ends_with_newline() -> None:
    """`raw=True` emits via opt(raw=True): no format prefix, guaranteed trailing newline."""
    stream = io.StringIO()
    sink_id = logger.add(stream, format="PREFIX>> {message}", level="DEBUG")
    try:
        loggerplusplus.info("banner-line", raw=True)
    finally:
        logger.remove(sink_id)
    out = stream.getvalue()
    assert "PREFIX>>" not in out  # the format prefix is bypassed in raw mode
    assert out == "banner-line\n"


def test_raw_mode_with_transform_and_multiline(cap: Any) -> None:
    """raw+transform emits the transformed text verbatim with a single trailing newline."""
    stream = io.StringIO()
    sink_id = logger.add(stream, format="PREFIX>> {message}", level="DEBUG")
    try:
        loggerplusplus.info("hi", raw=True, transform=Banner.box(align="left"))
    finally:
        logger.remove(sink_id)
    out = stream.getvalue()
    assert "PREFIX>>" not in out
    assert out.endswith("\n")
    assert not out.endswith("\n\n")  # exactly one trailing newline is ensured
    assert out.startswith("┌")


# --------------------------------------------------------------------------- caller attribution


def _capture_records() -> tuple:
    """Install a record-capturing sink; return (records, sink_id)."""
    records: List[dict] = []
    sink_id = logger.add(lambda m: records.append(m.record), format="{message}", level="DEBUG")
    return records, sink_id


def test_caller_attribution_transformed_points_to_test_file() -> None:
    """A transformed call is attributed to THIS test file, not to transform_proxy.py."""
    records, sink_id = _capture_records()
    try:
        loggerplusplus.info("x", transform=str.upper)
    finally:
        logger.remove(sink_id)
    rec = records[-1]
    assert rec["file"].name == "test_transform_proxy.py"
    assert rec["name"] == __name__
    # Exact identity guard: attribution must NOT land on the wrapper module.
    assert rec["name"] != "loggerplusplus.transform_proxy"
    assert rec["file"].name != "transform_proxy.py"


def test_caller_attribution_passthrough_points_to_test_file() -> None:
    """The passthrough fast path is also attributed to the caller, not the wrapper."""
    records, sink_id = _capture_records()
    try:
        loggerplusplus.info("x")  # no transform/raw -> fast path
    finally:
        logger.remove(sink_id)
    rec = records[-1]
    assert rec["file"].name == "test_transform_proxy.py"
    assert rec["name"] == __name__


def test_caller_attribution_on_bound_logger() -> None:
    """A bound TransformProxy also attributes to the caller (depth is preserved)."""
    records, sink_id = _capture_records()
    try:
        loggerplusplus.bind(identifier="TP_ATTR").info("x", transform=str.upper)
    finally:
        logger.remove(sink_id)
    rec = records[-1]
    assert rec["file"].name == "test_transform_proxy.py"


# --------------------------------------------------------------------------- non-regression


def test_bound_opt_returns_plain_loguru_logger(cap: Any) -> None:
    """`bound.opt(colors=True)` is loguru's opt: a plain Logger, NOT a TransformProxy."""
    bound = loggerplusplus.bind(identifier="TP_OPT")
    opted = bound.opt(colors=True)
    assert not isinstance(opted, TransformProxy)
    assert type(opted) is type(logger)  # a loguru Logger

    # Colored markup still renders (tags consumed, not emitted literally).
    cap.add(fmt="{message}")
    opted.info("<red>styled</red>")
    assert "<red>" not in cap.text
    assert "styled" in cap.text


def test_bound_catch_is_loguru_not_project_catch() -> None:
    """`bound.catch` stays loguru's catch, never the project decorator override."""
    bound = loggerplusplus.bind(identifier="TP_CATCH")
    assert bound.catch is not project_catch
    # It behaves as loguru's catch context manager (swallows by default).
    with bound.catch():
        raise ValueError("swallowed")


def test_chained_bind_rewraps_and_keeps_keyword(cap: Any) -> None:
    """Re-binding a bound TransformProxy returns another TransformProxy (keyword survives)."""
    cap.add(fmt="{extra[identifier]} {extra[sub]} {message}")
    chained = loggerplusplus.bind(identifier="TP_CHAIN").bind(sub="deep")
    assert isinstance(chained, TransformProxy)
    chained.info("hello", transform=str.upper)
    assert cap.text == "TP_CHAIN deep HELLO\n"


def test_transform_proxy_repr() -> None:
    """The proxy's repr identifies it as a TransformProxy wrapper."""
    bound = loggerplusplus.bind(identifier="TP_REPR")
    assert "TransformProxy" in repr(bound)
