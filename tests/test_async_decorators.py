# ====== Code Summary ======
# Tests for async-aware decorators (audit item A3): log_timing / log_io on `async def`
# must time and log the actual awaited execution, not the creation of the coroutine.

from __future__ import annotations

import asyncio
from typing import Any, List

import pytest
from loguru import logger

from loggerplusplus import log_io, log_timing


@pytest.fixture
def cap() -> Any:
    """Capture emitted log messages to a list, then remove the sink."""
    messages: List[str] = []
    sink_id = logger.add(messages.append, level="DEBUG", format="{message}")
    try:
        yield messages
    finally:
        logger.remove(sink_id)


def test_log_io_async_logs_awaited_result(cap: List[str]) -> None:
    """log_io on a coroutine logs the awaited value, not the coroutine object."""

    @log_io(log_args=False)
    async def compute(x: int) -> int:
        await asyncio.sleep(0)
        return x * 2

    result = asyncio.run(compute(21))
    assert result == 42
    text = "".join(cap)
    assert "returned 42" in text
    assert "coroutine" not in text


def test_log_io_async_logs_args(cap: List[str]) -> None:
    """log_io on a coroutine still logs the call arguments."""

    @log_io(log_return=False)
    async def greet(name: str) -> str:
        await asyncio.sleep(0)
        return "hi " + name

    asyncio.run(greet("bob"))
    assert "greet" in "".join(cap)
    assert "bob" in "".join(cap)


def test_log_timing_async_times_execution_and_returns(cap: List[str]) -> None:
    """log_timing on a coroutine times the awaited run and returns its value."""

    @log_timing(show_enter=False)
    async def work() -> int:
        await asyncio.sleep(0.02)
        return 7

    result = asyncio.run(work())
    assert result == 7
    text = "".join(cap)
    assert "Finished work" in text
    # The measured duration reflects the awaited sleep, not ~0.
    assert "in 0.000s" not in text


def test_log_timing_async_failure_is_timed_and_reraised(cap: List[str]) -> None:
    """A failing coroutine still logs a timed failure and re-raises."""

    @log_timing(show_enter=False)
    async def boom() -> None:
        await asyncio.sleep(0)
        raise ValueError("async nope")

    with pytest.raises(ValueError):
        asyncio.run(boom())
    text = "".join(cap)
    assert "Failed boom" in text
    assert "async nope" in text


def test_decorated_async_stays_a_coroutine_function() -> None:
    """The decorated async function is itself still a coroutine function."""

    @log_timing()
    async def w() -> int:
        return 1

    assert asyncio.iscoroutinefunction(w)


async def _consume(agen: Any) -> List[Any]:
    """Drain an async generator into a list."""
    return [item async for item in agen]


def test_log_io_async_generator_still_yields(cap: List[str]) -> None:
    """log_io on an async generator yields all items and does not log the generator object."""

    @log_io()
    async def gen(n: int) -> Any:
        for i in range(n):
            await asyncio.sleep(0)
            yield i

    items = asyncio.run(_consume(gen(3)))
    assert items == [0, 1, 2]
    text = "".join(cap)
    assert "Calling gen" in text
    assert "async_generator" not in text


def test_log_timing_async_generator_times_consumption(cap: List[str]) -> None:
    """log_timing on an async generator times the full consumption, not ~0."""

    @log_timing(show_enter=False)
    async def gen() -> Any:
        for _ in range(2):
            await asyncio.sleep(0.01)
            yield 1

    asyncio.run(_consume(gen()))
    text = "".join(cap)
    assert "Finished gen" in text
    assert "in 0.000s" not in text


def test_async_generator_error_reaches_on_error(cap: List[str]) -> None:
    """An exception raised while iterating an async generator reaches on_error."""

    @log_timing(show_enter=False)
    async def gen() -> Any:
        yield 1
        raise ValueError("gen boom")

    with pytest.raises(ValueError):
        asyncio.run(_consume(gen()))
    assert "Failed gen" in "".join(cap)


def test_cancellation_is_not_logged_as_failure(cap: List[str]) -> None:
    """A cancelled coroutine re-raises CancelledError without a 'Failed' log."""

    @log_timing(show_enter=False)
    async def slow() -> int:
        await asyncio.sleep(10)
        return 1

    async def run() -> None:
        task = asyncio.ensure_future(slow())
        await asyncio.sleep(0.01)
        task.cancel()
        await task

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(run())
    assert "Failed" not in "".join(cap)
