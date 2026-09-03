"""catch, log_timing, and log_io (with secret redaction) on sync and async functions."""

from __future__ import annotations

import asyncio
import sys
import time

from loggerplusplus import SENSITIVE_KEYS, add, catch, log_io, log_timing, remove


@log_timing(identifier="TASK", exit_message="Finished {func} in {duration:.3f}s")
@log_io(identifier="CALC", redact=SENSITIVE_KEYS)
def work(x: int, token: str) -> int:
    time.sleep(0.01)
    return x * 2


@log_timing(identifier="ASYNC")
async def fetch() -> str:
    await asyncio.sleep(0.01)
    return "payload"


@catch(identifier="RISKY", reraise=False)
def boom() -> None:
    raise RuntimeError("caught and logged, not re-raised")


def main() -> None:
    remove()
    add(sink=sys.stderr, level="DEBUG", format="[{identifier:<auto}] {message}")
    work(21, token="super-secret-value")  # 'token' is masked in the log
    asyncio.run(fetch())  # timed over the awaited execution
    boom()


if __name__ == "__main__":
    main()
