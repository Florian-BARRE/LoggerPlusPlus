# ====== Code Summary ======
# Phase 3 characterization (safety net) for the structured-JSON boundary: the public
# add_json() sink and the JSON path it configures. These tests pin the CURRENT rendered
# payload — the exact key set, the frozen-time serialization, bind/bind_context routing,
# exception serialization and the non-serializable-degradation path — so a later
# behaviour-preserving refactoring can prove it changed nothing.
#
# Determinism: the clock (loguru._logger.aware_now) and the process/thread ids
# (os.getpid / threading.get_ident) are frozen so the time/process/thread fields are
# byte-stable. The name/function/line/module fields are the call-site of the fixed
# helper functions below, which is stable for this file.

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict
from unittest import mock

import pytest

from loggerplusplus import add_json, bind_context, logger

# ----- frozen, deterministic inputs -------------------------------------------------
FIXED = datetime(2020, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)
PID = 4242
TID = 1


# ----- call-site helpers (their line numbers are part of the goldens) --------------
def _emit_representative() -> None:
    logger.bind(identifier="SVC", user="bob").info("hello world")


def _emit_two() -> None:
    logger.bind(identifier="A").info("first")
    logger.bind(identifier="B", user="x").warning("second")


def _emit_cyclic() -> None:
    loop: Dict[str, Any] = {}
    loop["self"] = loop
    logger.bind(loop=loop).info("cyclic")


def _emit_raising() -> None:
    class _Bad:
        def __repr__(self) -> str:
            raise RuntimeError("no repr")

        def __str__(self) -> str:
            raise RuntimeError("no str")

    logger.bind(bad=_Bad()).info("weird")


def _emit_exception() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("failed")


def _emit_context() -> None:
    with bind_context(request_id="req-1", correlation_id="cor-1"):
        logger.info("ctx msg")


def _last_json(cap: "object") -> Dict[str, Any]:
    """Parse the most recent captured record (the add_json sink is the only one active)."""
    return json.loads(str(cap.buf[-1]))


@pytest.fixture
def frozen() -> None:
    """Freeze the clock and the process/thread ids for the duration of the test."""
    with (
        mock.patch("loguru._logger.aware_now", return_value=FIXED),
        mock.patch("os.getpid", return_value=PID),
        mock.patch("threading.get_ident", return_value=TID),
    ):
        yield


def _add(cap: "object", **kwargs: Any) -> None:
    """Install an add_json sink on the shared capture and track it for teardown."""
    cap.track(add_json(sink=cap.append, level="DEBUG", **kwargs))


# 1. one JSON object per record -----------------------------------------------------
def test_single_record_is_one_json_object(cap: "object", frozen: None) -> None:
    """One record produces exactly one sink write that is a single valid JSON object."""
    _add(cap)
    _emit_representative()
    assert len(cap.buf) == 1
    assert isinstance(cap.buf[0], str)
    assert isinstance(json.loads(cap.buf[0]), dict)


# 2. exact, ordered key set ---------------------------------------------------------
def test_payload_has_exactly_the_documented_key_set(
    cap: "object", frozen: None
) -> None:
    """The representative record serializes to exactly the documented top-level keys, in order."""
    _add(cap)
    _emit_representative()
    obj = _last_json(cap)
    assert list(obj.keys()) == GOLDEN_REP_KEYS
    assert set(obj.keys()) == set(GOLDEN_REP_KEYS)


# 3. frozen time --------------------------------------------------------------------
def test_frozen_time_key_is_iso_stable(cap: "object", frozen: None) -> None:
    """With the clock frozen, the time key is the frozen datetime's ISO-8601 form."""
    _add(cap)
    _emit_representative()
    assert _last_json(cap)["time"] == GOLDEN_TIME


# 4. full representative golden ------------------------------------------------------
def test_representative_record_golden(cap: "object", frozen: None) -> None:
    """The whole representative record matches its locked JSON byte-for-byte."""
    _add(cap)
    _emit_representative()
    assert cap.buf[0] == GOLDEN_REP


# 5. bind: identifier promoted, rest in extra ----------------------------------------
def test_bind_promotes_identifier_and_keeps_rest_in_extra(
    cap: "object", frozen: None
) -> None:
    """bind(identifier=...) is promoted to the top level; other bind fields stay in extra."""
    _add(cap)
    _emit_representative()
    obj = _last_json(cap)
    assert obj["identifier"] == "SVC"
    assert obj["extra"] == {"user": "bob"}
    assert "identifier" not in obj["extra"]


# 6. bind_context lands in extra ------------------------------------------------------
def test_bind_context_fields_landed_in_extra(cap: "object", frozen: None) -> None:
    """Fields bound via bind_context appear under the documented extra key."""
    _add(cap)
    _emit_context()
    obj = _last_json(cap)
    assert obj["extra"] == {"request_id": "req-1", "correlation_id": "cor-1"}
    assert obj["identifier"] is None


# 7. circular-reference extra degrades -----------------------------------------------
def test_circular_extra_degrades_to_error_payload(cap: "object", frozen: None) -> None:
    """A circular-reference extra degrades to a valid degraded line, not a dropped record."""
    _add(cap)
    _emit_cyclic()
    obj = _last_json(cap)
    assert set(obj.keys()) == {"level", "message", "_lpp_json_error"}
    assert obj["level"] == "INFO"
    assert obj["message"] == "cyclic"
    assert "Circular reference" in obj["_lpp_json_error"]


# 8. raising str() extra degrades -----------------------------------------------------
def test_raising_str_extra_degrades_to_error_payload(
    cap: "object", frozen: None
) -> None:
    """An extra whose str()/repr() raise still yields a valid degraded line."""
    _add(cap)
    _emit_raising()
    obj = _last_json(cap)
    assert set(obj.keys()) == {"level", "message", "_lpp_json_error"}
    assert obj["message"] == "weird"
    assert "no str" in obj["_lpp_json_error"]


# 9. exception record ----------------------------------------------------------------
def test_exception_record_serialized(cap: "object", frozen: None) -> None:
    """logger.exception serializes the exception as a structured type/value/traceback."""
    _add(cap)
    _emit_exception()
    obj = _last_json(cap)
    assert obj["level"] == "ERROR"
    exc = obj["exception"]
    assert exc["type"] == "ValueError"
    assert exc["value"] == "boom"
    assert isinstance(exc["traceback"], str)
    assert "ValueError" in exc["traceback"]


# 10. non-exception record ------------------------------------------------------------
def test_non_exception_record_has_null_exception(cap: "object", frozen: None) -> None:
    """A record without an exception carries a null exception field."""
    _add(cap)
    _emit_representative()
    assert _last_json(cap)["exception"] is None


# 11. fields filter -------------------------------------------------------------------
def test_fields_restricts_payload_keys(cap: "object", frozen: None) -> None:
    """fields= keeps only the requested top-level keys, serialized exactly as pinned."""
    _add(cap, fields=("level", "message"))
    logger.bind(identifier="SVC").info("hi")
    assert cap.buf[0] == GOLDEN_FIELDS
    assert set(json.loads(cap.buf[0]).keys()) == {"level", "message"}


# 12. NDJSON / newline behaviour (bug-like: pin current output) -----------------------
def test_file_sink_records_are_not_newline_delimited(
    frozen: None, tmp_path: Any
) -> None:
    """CURRENT behaviour: a file sink writes records back-to-back with NO newline.

    The docs advertise a "newline-delimited JSON file", but add_json passes loguru a
    *callable* format and loguru only appends its terminator to *string* formats, so no
    separator is emitted. This golden pins what the code does today; if the newline is
    ever added, this test flips (and the docs finally match).
    """
    target = str(tmp_path / "structured.jsonl")
    sink_id = add_json(sink=target, level="DEBUG")
    _emit_two()
    logger.remove(sink_id)
    raw = open(target, "rb").read()
    assert b"\n" not in raw
    assert raw.decode() == GOLDEN_NDJSON


# ----- goldens (read from the run above; byte-stable) ------------------------------
GOLDEN_TIME = "2020-01-02T03:04:05.123456+00:00"
GOLDEN_REP_KEYS = [
    "time",
    "level",
    "identifier",
    "message",
    "name",
    "function",
    "line",
    "module",
    "process",
    "thread",
    "extra",
    "exception",
]
GOLDEN_REP = (
    '{"time": "2020-01-02T03:04:05.123456+00:00", "level": "INFO", '
    '"identifier": "SVC", "message": "hello world", '
    '"name": "tests.test_char_structured", "function": "_emit_representative", '
    '"line": 32, "module": "test_char_structured", "process": 4242, '
    '"thread": 1, "extra": {"user": "bob"}, "exception": null}'
)
GOLDEN_FIELDS = '{"level": "INFO", "message": "hi"}'
GOLDEN_NDJSON = (
    '{"time": "2020-01-02T03:04:05.123456+00:00", "level": "INFO", '
    '"identifier": "A", "message": "first", "name": "tests.test_char_structured", '
    '"function": "_emit_two", "line": 36, "module": "test_char_structured", '
    '"process": 4242, "thread": 1, "extra": {}, "exception": null}'
    '{"time": "2020-01-02T03:04:05.123456+00:00", "level": "WARNING", '
    '"identifier": "B", "message": "second", "name": "tests.test_char_structured", '
    '"function": "_emit_two", "line": 37, "module": "test_char_structured", '
    '"process": 4242, "thread": 1, "extra": {"user": "x"}, "exception": null}'
)
