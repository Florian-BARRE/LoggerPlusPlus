# ====== Code Summary ======
# Tests for add_json (audit item A4): structured JSON output. Each record is emitted as
# one JSON object with a clean schema (identifier promoted, internal extra keys excluded,
# structured exception), usable with a stream, callable, or file sink.

from __future__ import annotations

import json
from typing import Any, List

import pytest
from loguru import logger

from loggerplusplus import add_json


@pytest.fixture
def jsonlines() -> Any:
    """Install a JSON sink writing to a list; remove it afterward."""
    lines: List[str] = []
    sink_id = add_json(sink=lines.append, level="DEBUG")
    try:
        yield lines
    finally:
        logger.remove(sink_id)


def test_add_json_basic_schema(jsonlines: List[str]) -> None:
    """A record serializes to JSON with identifier promoted and extra preserved."""
    logger.bind(identifier="SVC", user="bob").info("hello")
    obj = json.loads(jsonlines[-1])
    assert obj["level"] == "INFO"
    assert obj["identifier"] == "SVC"
    assert obj["message"] == "hello"
    assert obj["extra"]["user"] == "bob"
    assert "identifier" not in obj["extra"]  # promoted to the top level


def test_add_json_excludes_internal_extra(jsonlines: List[str]) -> None:
    """Internal machinery keys never leak into the payload's extra."""
    logger.bind(_lpp_secret="x", real="y").info("m")
    obj = json.loads(jsonlines[-1])
    assert obj["extra"] == {"real": "y"}
    assert "_lpp_json" not in obj["extra"]


def test_add_json_serializes_exception(jsonlines: List[str]) -> None:
    """An exception is serialized as a structured object with a traceback."""
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("failed")
    obj = json.loads(jsonlines[-1])
    assert obj["exception"]["type"] == "ValueError"
    assert obj["exception"]["value"] == "boom"
    assert "ValueError" in obj["exception"]["traceback"]


def test_add_json_no_exception_is_null(jsonlines: List[str]) -> None:
    """A normal record has a null exception field."""
    logger.info("fine")
    assert json.loads(jsonlines[-1])["exception"] is None


def test_add_json_fields_filter() -> None:
    """`fields` restricts the payload to the requested top-level keys."""
    lines: List[str] = []
    sink_id = add_json(sink=lines.append, level="DEBUG", fields=("level", "message"))
    try:
        logger.info("hi")
        obj = json.loads(lines[-1])
        assert set(obj) == {"level", "message"}
    finally:
        logger.remove(sink_id)


def test_add_json_keeps_unicode(jsonlines: List[str]) -> None:
    """ensure_ascii=False keeps non-ASCII readable in the output."""
    logger.bind(identifier="日本").info("héllo")
    obj = json.loads(jsonlines[-1])
    assert obj["identifier"] == "日本"
    assert "日本" in jsonlines[-1]


def test_add_json_serializes_unusual_extra(jsonlines: List[str]) -> None:
    """A non-JSON-native extra value is coerced via default=str rather than crashing."""
    logger.bind(obj=object()).info("m")
    obj = json.loads(jsonlines[-1])
    assert isinstance(obj["extra"]["obj"], str)


def test_add_json_survives_circular_reference(jsonlines: List[str]) -> None:
    """A circular-reference extra degrades to a valid line instead of dropping the record."""
    loop: dict = {}
    loop["self"] = loop
    logger.bind(loop=loop).info("cyclic")
    obj = json.loads(jsonlines[-1])
    assert obj["message"] == "cyclic"
    assert "_lpp_json_error" in obj


def test_add_json_survives_raising_str(jsonlines: List[str]) -> None:
    """An extra whose str()/repr() raises still produces a valid, non-dropped line."""

    class Bad:
        def __repr__(self) -> str:
            raise RuntimeError("no repr")

        def __str__(self) -> str:
            raise RuntimeError("no str")

    logger.bind(bad=Bad()).info("weird")
    obj = json.loads(jsonlines[-1])
    assert obj["message"] == "weird"
    assert "_lpp_json_error" in obj


def test_add_json_does_not_pollute_later_sinks() -> None:
    """The internal serialization key never leaks into a sink ordered after add_json."""
    seen: List[dict] = []
    json_id = add_json(sink=lambda m: None, level="DEBUG")
    plain_id = logger.add(
        lambda m: seen.append(dict(m.record["extra"])),
        level="DEBUG",
        format="{message}",
    )
    try:
        logger.info("x")
        assert seen and all("_lpp_json" not in extra for extra in seen)
    finally:
        logger.remove(json_id)
        logger.remove(plain_id)


def test_add_json_to_file(tmp_path: Any) -> None:
    """add_json works with a file-path sink (loguru manages the file)."""
    logfile = tmp_path / "structured.log"
    sink_id = add_json(sink=str(logfile), level="DEBUG")
    logger.bind(identifier="F").info("filejson")
    logger.remove(sink_id)  # flush + close
    last = logfile.read_text().strip().splitlines()[-1]
    obj = json.loads(last)
    assert obj["message"] == "filejson"
    assert obj["identifier"] == "F"
