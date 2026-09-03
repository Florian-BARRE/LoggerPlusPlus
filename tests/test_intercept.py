# ====== Code Summary ======
# Tests for intercept_std_logging (audit item A1): standard-library logging records
# are routed through loguru with the right level and an identifier. Global logging
# state is saved and restored around each test.

from __future__ import annotations

import logging
from typing import Any, List

import pytest
from loguru import logger

from loggerplusplus import InterceptHandler, intercept_std_logging

_LOGGER_NAME = "lpp_intercept_test"


@pytest.fixture
def loguru_cap() -> Any:
    """Capture intercepted loguru records as 'identifier|LEVEL|message' lines."""
    messages: List[str] = []
    sink_id = logger.add(
        messages.append,
        level="TRACE",
        format="{extra[identifier]}|{level.name}|{message}",
        filter=lambda r: "identifier" in r["extra"],
    )
    try:
        yield messages
    finally:
        logger.remove(sink_id)


@pytest.fixture
def std_logger() -> Any:
    """Yield a throwaway named logger and restore its config afterward."""
    lg = logging.getLogger(_LOGGER_NAME)
    saved = (lg.handlers[:], lg.propagate, lg.level)
    try:
        yield lg
    finally:
        lg.handlers, lg.propagate, lg.level = saved


def test_intercept_routes_module_logging(
    loguru_cap: List[str], std_logger: Any
) -> None:
    """A stdlib record on the intercepted logger is re-emitted through loguru."""
    intercept_std_logging(modules=[_LOGGER_NAME])
    logging.getLogger(_LOGGER_NAME).warning("hello from std")
    text = "".join(loguru_cap)
    assert "hello from std" in text
    assert "WARNING" in text
    assert _LOGGER_NAME in text  # identifier defaults to the logger name


def test_intercept_fixed_identifier(loguru_cap: List[str], std_logger: Any) -> None:
    """A fixed identifier is bound on every intercepted record."""
    intercept_std_logging(modules=[_LOGGER_NAME], identifier="THIRDPARTY")
    logging.getLogger(_LOGGER_NAME).error("boom")
    text = "".join(loguru_cap)
    assert "THIRDPARTY|ERROR|boom" in text


def test_intercept_returns_handler(std_logger: Any) -> None:
    """The installed forwarding handler is returned."""
    handler = intercept_std_logging(modules=[_LOGGER_NAME])
    assert isinstance(handler, InterceptHandler)


def test_intercept_respects_std_level(loguru_cap: List[str], std_logger: Any) -> None:
    """The level set on the intercepted logger filters before forwarding."""
    intercept_std_logging(modules=[_LOGGER_NAME], level=logging.ERROR)
    logging.getLogger(_LOGGER_NAME).warning("suppressed")
    logging.getLogger(_LOGGER_NAME).error("shown")
    text = "".join(loguru_cap)
    assert "suppressed" not in text
    assert "shown" in text


def test_intercept_forwards_exception_info(
    loguru_cap: List[str], std_logger: Any
) -> None:
    """`logging.exception(...)` carries its traceback through to loguru."""
    intercept_std_logging(modules=[_LOGGER_NAME])
    try:
        raise ValueError("kaboom")
    except ValueError:
        logging.getLogger(_LOGGER_NAME).exception("caught it")
    text = "".join(loguru_cap)
    assert "caught it" in text


def test_intercept_unknown_level_falls_back_to_number(
    loguru_cap: List[str], std_logger: Any
) -> None:
    """A stdlib level name loguru does not know falls back to the numeric level."""
    logging.addLevelName(25, "NOTICE_LPP")
    intercept_std_logging(modules=[_LOGGER_NAME], level=logging.DEBUG)
    logging.getLogger(_LOGGER_NAME).log(25, "noticed")
    assert "noticed" in "".join(loguru_cap)


def test_intercept_root_logger() -> None:
    """With no modules, the root logger is taken over and any logger routes through loguru."""
    root = logging.getLogger()
    saved = (root.handlers[:], root.level)
    messages: List[str] = []
    sink_id = logger.add(
        messages.append,
        level="TRACE",
        format="{extra[identifier]}|{message}",
        filter=lambda r: "identifier" in r["extra"],
    )
    try:
        intercept_std_logging()
        logging.getLogger("some.random.lib").info("root routed")
        assert "some.random.lib|root routed" in "".join(messages)
    finally:
        logger.remove(sink_id)
        root.handlers, root.level = saved
