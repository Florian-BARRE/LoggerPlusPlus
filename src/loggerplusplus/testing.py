# ====== Code Summary ======
# Test helpers for asserting log output in downstream projects: a `capture()` context
# manager that installs a temporary loguru sink and collects the records and rendered
# messages. No pytest dependency — wrap it in your own fixture if you want one.

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

from loguru import logger as _loguru_logger

__all__: list[str] = ["capture", "LogCapture"]


class LogCapture:
    """
    Collects captured log records and their rendered messages.

    Attributes:
        records (list[dict]): The captured loguru records (shallow copies).
        messages (list[str]): The rendered message strings.
    """

    def __init__(self) -> None:
        """Initialize empty capture buffers."""
        self.records: List[Dict[str, Any]] = []
        self.messages: List[str] = []

    @property
    def text(self) -> str:
        """All rendered messages joined into one string."""
        return "".join(self.messages)

    def __contains__(self, substring: object) -> bool:
        """True if `substring` appears anywhere in the captured text."""
        return str(substring) in self.text

    def __len__(self) -> int:
        """Number of captured records."""
        return len(self.records)


@contextmanager
def capture(*, level: Any = "TRACE", format: str = "{message}") -> Iterator[LogCapture]:
    """
    Capture log records emitted within the block into a `LogCapture`.

    Example:
        with capture() as cap:
            logger.bind(identifier="X").info("hello")
        assert "hello" in cap
        assert cap.records[-1]["extra"]["identifier"] == "X"

    Args:
        level (int | str): Minimum level to capture (default "TRACE" — everything).
        format (str): Message format for `messages`/`text` (default the raw message).

    Yields:
        LogCapture: The buffer, populated as records are emitted.
    """
    # 1. Install a temporary sink collecting each record and its rendered message.
    cap = LogCapture()

    def _sink(message: Any) -> None:
        cap.records.append(dict(message.record))
        cap.messages.append(str(message))

    sink_id = _loguru_logger.add(_sink, level=level, format=format)
    try:
        yield cap
    finally:
        # 2. Always remove the temporary sink.
        _loguru_logger.remove(sink_id)
