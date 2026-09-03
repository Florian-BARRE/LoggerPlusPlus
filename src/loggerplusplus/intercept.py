# ====== Code Summary ======
# Route the standard library `logging` into loguru, so third-party libraries (uvicorn,
# SQLAlchemy, requests, ...) that log via `logging` are rendered through the same
# LoggerPlusPlus sinks/format instead of their own raw handlers.

from __future__ import annotations

import inspect
import logging
from typing import Any, Iterable, Optional

from loguru import logger as _loguru_logger

__all__: list[str] = ["intercept_std_logging", "InterceptHandler"]


class InterceptHandler(logging.Handler):
    """
    A `logging.Handler` that forwards standard-library records to loguru.

    Each record is re-emitted at the matching loguru level, from the correct call site
    (so `{name}:{line}` points at the original caller, not the logging internals), and
    bound with an `identifier` — the record's logger name by default, or a fixed value.
    """

    def __init__(self, identifier: Optional[str] = None) -> None:
        """
        Args:
            identifier (str | None): Identifier to bind on intercepted records; when None,
                the record's own logger name is used (so third-party logs are labeled by source).
        """
        super().__init__()
        self._identifier = identifier

    def emit(self, record: logging.LogRecord) -> None:
        """Forward a standard-library log record to loguru."""
        # 1. Map the stdlib level name to a loguru level (fall back to the numeric level).
        level: Any
        try:
            level = _loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 2. Walk out of the logging module so the caller's file/line is reported.
        frame: Any = inspect.currentframe()
        depth = 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        # 3. Bind an identifier (fixed, or the source logger name) and re-emit.
        ident = self._identifier if self._identifier is not None else record.name
        _loguru_logger.bind(identifier=ident).opt(
            depth=depth, exception=record.exc_info
        ).log(level, record.getMessage())


def intercept_std_logging(
    level: int = logging.NOTSET,
    *,
    modules: Optional[Iterable[str]] = None,
    identifier: Optional[str] = None,
) -> InterceptHandler:
    """
    Route the standard library `logging` into loguru (opt-in; never called at import).

    Call this once during application start-up so libraries that use `logging` flow through
    your LoggerPlusPlus sinks and format. By default it takes over the root logger; pass
    `modules` to intercept only specific logger trees (e.g. "uvicorn", "sqlalchemy").

    Args:
        level (int): Minimum level for the intercepted logger(s). Default NOTSET: the root
            logger then captures everything (your loguru sink decides what is shown), but a
            SPECIFIC module inherits its parent's level (typically WARNING) — pass an explicit
            level (e.g. logging.DEBUG) to capture below that.
        modules (Iterable[str] | None): Specific logger names to intercept; None takes over
            the root logger (replacing its handlers).
        identifier (str | None): Identifier bound on intercepted records; None uses each
            record's own logger name.

    Returns:
        InterceptHandler: The installed handler (so it can be removed later if desired).
    """
    # 1. Build the forwarding handler.
    handler = InterceptHandler(identifier=identifier)

    # 2. Install it on the root logger, or on each named logger tree.
    if modules is None:
        logging.basicConfig(handlers=[handler], level=level, force=True)
    else:
        for name in modules:
            std_logger = logging.getLogger(name)
            std_logger.handlers = [handler]
            std_logger.propagate = False
            std_logger.setLevel(level)

    return handler
