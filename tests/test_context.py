# ====== Code Summary ======
# Tests for correlation context (audit item A5): bind_context scopes fields onto records
# within a block (correctly under asyncio via contextvars), new_id generates ids, and
# otel_context degrades gracefully when OpenTelemetry is absent.

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import pytest
from loguru import logger

from loggerplusplus import bind_context, new_id, otel_context


@pytest.fixture
def extras() -> Any:
    """Capture each record's `extra` dict."""
    captured: List[Dict[str, Any]] = []
    sink_id = logger.add(
        lambda m: captured.append(dict(m.record["extra"])),
        level="DEBUG",
        format="{message}",
    )
    try:
        yield captured
    finally:
        logger.remove(sink_id)


def test_bind_context_scopes_fields(extras: List[Dict[str, Any]]) -> None:
    """Fields are bound inside the block and gone outside it."""
    with bind_context(user="bob", correlation_id="C1"):
        logger.info("inside")
    logger.info("outside")
    assert extras[0]["user"] == "bob"
    assert extras[0]["correlation_id"] == "C1"
    assert "user" not in extras[1]
    assert "correlation_id" not in extras[1]


def test_bind_context_request_id(extras: List[Dict[str, Any]]) -> None:
    """A request id is bound under `request_id`."""
    rid = new_id(prefix="req-")
    with bind_context(request_id=rid):
        logger.info("x")
    assert extras[-1]["request_id"] == rid


def test_new_id_unique_and_shaped() -> None:
    """new_id is unique, length-controlled, and honors a prefix."""
    assert new_id() != new_id()
    assert len(new_id()) == 12
    assert len(new_id(length=8)) == 8
    assert new_id(prefix="r-", length=8).startswith("r-")


def test_otel_context_empty_without_opentelemetry() -> None:
    """Without OpenTelemetry (or an active span), otel_context is an empty dict."""
    assert otel_context() == {}


def _install_fake_otel(monkeypatch: Any, *, valid: bool) -> None:
    """Inject a minimal fake `opentelemetry` module exposing a current span."""
    import sys
    import types

    class _Ctx:
        is_valid = valid
        trace_id = 0x1234
        span_id = 0xABCD

    class _Span:
        def get_span_context(self) -> _Ctx:
            return _Ctx()

    fake = types.ModuleType("opentelemetry")
    fake.trace = types.SimpleNamespace(get_current_span=lambda: _Span())  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "opentelemetry", fake)


def test_otel_context_reads_current_span(monkeypatch: Any) -> None:
    """With an OTel span present, trace/span ids are returned as hex."""
    _install_fake_otel(monkeypatch, valid=True)
    result = otel_context()
    assert result["trace_id"] == format(0x1234, "032x")
    assert result["span_id"] == format(0xABCD, "016x")


def test_otel_context_ignores_invalid_span(monkeypatch: Any) -> None:
    """An invalid (no-op) span yields an empty context."""
    _install_fake_otel(monkeypatch, valid=False)
    assert otel_context() == {}


def _install_broken_otel(monkeypatch: Any) -> None:
    """Inject a fake `opentelemetry` whose span read raises (a broken install)."""
    import sys
    import types

    def _boom() -> Any:
        raise RuntimeError("broken otel")

    fake = types.ModuleType("opentelemetry")
    fake.trace = types.SimpleNamespace(get_current_span=_boom)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "opentelemetry", fake)


def test_otel_context_broken_install_returns_empty(monkeypatch: Any) -> None:
    """A broken OpenTelemetry install yields an empty context, not an exception."""
    _install_broken_otel(monkeypatch)
    assert otel_context() == {}


def test_bind_context_broken_otel_does_not_raise(
    monkeypatch: Any, extras: List[Dict[str, Any]]
) -> None:
    """bind_context(otel=True) never propagates a broken-OTel error into the call site."""
    _install_broken_otel(monkeypatch)
    with bind_context(otel=True, k="v"):
        logger.info("x")
    assert extras[-1]["k"] == "v"
    assert "trace_id" not in extras[-1]


def test_bind_context_otel_flag_is_harmless(extras: List[Dict[str, Any]]) -> None:
    """otel=True adds nothing when OTel is unavailable but still binds other fields."""
    with bind_context(otel=True, foo="bar"):
        logger.info("x")
    assert extras[-1]["foo"] == "bar"
    assert "trace_id" not in extras[-1]


def test_bind_context_is_async_task_scoped(extras: List[Dict[str, Any]]) -> None:
    """Concurrent tasks each keep their own bound context (contextvars)."""

    async def worker(tag: str) -> None:
        with bind_context(task=tag):
            await asyncio.sleep(0)
            logger.info("t")

    async def main() -> None:
        await asyncio.gather(worker("A"), worker("B"))

    asyncio.run(main())
    tags = sorted(e.get("task") for e in extras if "task" in e)
    assert tags == ["A", "B"]
