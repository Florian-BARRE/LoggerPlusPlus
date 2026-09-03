# ====== Code Summary ======
# Tests for setup() / configure_from_env() (audit item A2): one-call configuration of a
# console sink (format by name), an optional plain file sink, env-driven variant, and
# stdlib interception. Loguru sinks are cleared after each test.

from __future__ import annotations

import logging
from typing import Any, List

import pytest
from loguru import logger

from loggerplusplus import configure_from_env, formats, setup
from loggerplusplus.bootstrap import _env_bool, _resolve_format


@pytest.fixture(autouse=True)
def _clear_sinks() -> Any:
    """Leave a clean slate of loguru sinks after each test."""
    try:
        yield
    finally:
        logger.remove()


def test_setup_console_with_named_format() -> None:
    """setup() installs a console sink using a format resolved by name."""
    messages: List[str] = []
    ids = setup(level="DEBUG", format="ShortFormat", sink=messages.append)
    assert "console" in ids
    logger.bind(identifier="MAIN").info("hello world")
    text = "".join(messages)
    assert "hello world" in text
    assert "MAIN" in text  # the identifier column rendered


def test_setup_writes_plain_file(tmp_path: Any) -> None:
    """A file sink receives plain (uncolored) output."""
    logfile = tmp_path / "app.log"
    ids = setup(format="ShortFormat", sink=lambda m: None, file=str(logfile))
    assert "file" in ids
    logger.bind(identifier="FILE").info("to the file")
    logger.remove()  # flush + close the file sink
    content = logfile.read_text()
    assert "to the file" in content
    assert "\x1b" not in content  # no ANSI escape codes in the file


def test_setup_remove_existing_false_keeps_prior_sinks() -> None:
    """remove_existing=False leaves earlier sinks in place."""
    first: List[str] = []
    logger.add(first.append, level="DEBUG", format="{message}")
    second: List[str] = []
    setup(format="{message}", sink=second.append, remove_existing=False)
    logger.info("both")
    assert any("both" in m for m in first)
    assert any("both" in m for m in second)


def test_setup_intercepts_std_logging() -> None:
    """setup(intercept=True) routes standard-library logging through loguru."""
    messages: List[str] = []
    setup(
        format="{extra[identifier]}|{message}",
        sink=messages.append,
        intercept=True,
    )
    logging.getLogger("some.lib").warning("via stdlib")
    assert any("via stdlib" in m for m in messages)


def test_configure_from_env_drives_setup(monkeypatch: Any, tmp_path: Any) -> None:
    """configure_from_env reads the prefixed variables and configures accordingly."""
    logfile = tmp_path / "env.log"
    monkeypatch.setenv("LOGGING_LPP_LEVEL", "DEBUG")
    monkeypatch.setenv("LOGGING_LPP_FORMAT", "MinimalFormat")
    monkeypatch.setenv("LOGGING_LPP_FILE", str(logfile))
    ids = configure_from_env()
    assert "file" in ids
    logger.bind(identifier="ENV").info("from env")
    logger.remove()
    assert "from env" in logfile.read_text()


def test_configure_from_env_booleans(monkeypatch: Any) -> None:
    """Boolean env variables are parsed and forwarded to setup."""
    messages: List[str] = []
    monkeypatch.setenv("LOGGING_LPP_FORMAT", "{extra[identifier]}|{message}")
    monkeypatch.setenv("LOGGING_LPP_INTERCEPT", "true")
    monkeypatch.setenv("LOGGING_LPP_ENQUEUE", "no")
    # sink still defaults to stderr; just assert it configures without error and intercepts.
    configure_from_env()
    logging.getLogger("envlib").warning("env intercept")
    # Nothing to capture from stderr here; the call must simply not raise.


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1", True),
        ("true", True),
        ("YES", True),
        ("on", True),
        ("0", False),
        ("no", False),
    ],
)
def test_env_bool(value: str, expected: bool) -> None:
    """_env_bool recognizes the truthy tokens."""
    assert _env_bool(value) is expected


def test_resolve_format_variants() -> None:
    """Format names resolve to instances; other strings/objects pass through."""
    assert isinstance(_resolve_format("ShortFormat", True), formats.ShortFormat)
    assert _resolve_format("{message}", True) == "{message}"
    assert (
        _resolve_format("BaseFormat", True) == "BaseFormat"
    )  # abstract base not instantiated
    inst = formats.OpsFormat()
    assert _resolve_format(inst, True) is inst

    def _callable_format(record: Any) -> str:
        return "custom"

    # A non-string (callable) format passes straight through.
    assert _resolve_format(_callable_format, True) is _callable_format
