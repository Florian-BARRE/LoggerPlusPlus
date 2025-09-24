# loggerPlusPlus/decorators.py
# ====== Code Summary ======
# Convenience decorators and wrappers around `loguru` that:
# - provide optional identifier binding (via `extra['identifier']`),
# - expose `catch` and `opt` helpers that respect a passed logger or identifier,
# - add decorators to log execution timing and I/O (arguments/return values).
# Designed to be drop-in friendly for operational and debugging use.

from __future__ import annotations

# ====== Standard Library Imports ======
import functools
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

# ====== Third-Party Library Imports ======
from loguru import logger as _loguru_logger

__all__: list[str] = ["catch", "opt", "log_timing", "log_io"]

P = ParamSpec("P")
R = TypeVar("R")


def _select_logger(logger: Any | None = None, identifier: str | None = None) -> Any:
    """
    Select an appropriate logger, optionally binding an identifier.

    Args:
        logger (Any | None): A pre-bound logger to use if provided.
        identifier (str | None): If provided and no `logger` is passed, bind this
            identifier to the global loguru logger.

    Returns:
        Any: A logger-like object (loguru `Logger` or bound proxy).

    Steps:
        # 1. If a logger is explicitly provided, return it as-is.
        # 2. Otherwise, bind identifier to the global logger when given.
        # 3. Fallback to the global logger unchanged.
    """
    # 1. If a logger is explicitly provided, return it as-is.
    if logger is not None:
        return logger
    # 2. Otherwise, bind identifier to the global logger when given.
    # 3. Fallback to the global logger unchanged.
    return _loguru_logger.bind(identifier=identifier) if identifier else _loguru_logger


def catch(
        *decorator_args: Any,
        identifier: str | None = None,
        logger: Any | None = None,
        **decorator_kwargs: Any,
):
    """
    Drop-in replacement for loguru.logger.catch with extra convenience:
      - `identifier`: bind an identifier for caught exceptions
      - `logger`: pass an already-bound logger (takes precedence)

    Usage:
        @catch()                       # same as loguru.logger.catch()
        @catch(identifier="SERVICE")
        @catch(logger=my_bound_logger, level="WARNING")

        with catch(identifier="BATCH", level="ERROR"):
            ...

    Args:
        *decorator_args (Any): Positional arguments forwarded to `logger.catch`.
        identifier (str | None): Optional identifier to bind when no logger is provided.
        logger (Any | None): Optional pre-bound logger instance (takes precedence).
        **decorator_kwargs (Any): Keyword arguments forwarded to `logger.catch`.

    Returns:
        Any: The value returned by `logger.catch` (decorator or context manager).

    Steps:
        # 1. Resolve the effective logger (prefer provided `logger`, else bind identifier).
        # 2. Delegate to the logger's `catch` with all original arguments.
    """
    # 1. Resolve the effective logger (prefer provided `logger`, else bind identifier).
    bound = _select_logger(logger=logger, identifier=identifier)
    # 2. Delegate to the logger's `catch` with all original arguments.
    return bound.catch(*decorator_args, **decorator_kwargs)


def opt(
        *args: Any,
        identifier: str | None = None,
        logger: Any | None = None,
        **kwargs: Any,
):
    """
    Convenience wrapper for logger.opt() with optional identifier or pre-bound logger.

    Example:
        log = opt(depth=1, identifier="JOB42")
        log.info("Hello")

        bound = logger.bind(identifier="API")
        log2 = opt(logger=bound, colors=True)
        log2.warning("Heads up")

    Args:
        *args (Any): Positional arguments forwarded to `logger.opt`.
        identifier (str | None): Optional identifier to bind when no logger is provided.
        logger (Any | None): Optional pre-bound logger instance (takes precedence).
        **kwargs (Any): Keyword arguments forwarded to `logger.opt`.

    Returns:
        Any: The result from `logger.opt` (an `Opt` logger proxy).

    Steps:
        # 1. Resolve the effective logger (prefer provided `logger`, else bind identifier).
        # 2. Delegate to the logger's `opt` with all original arguments.
    """
    # 1. Resolve the effective logger (prefer provided `logger`, else bind identifier).
    bound = _select_logger(logger=logger, identifier=identifier)
    # 2. Delegate to the logger's `opt` with all original arguments.
    return bound.opt(*args, **kwargs)


def log_timing(
        *,
        logger: Any | None = None,
        identifier: str | None = None,
        level: str = "DEBUG",
        enter_message: str | None = None,
        exit_message: str = "Finished {func} in {duration:.3f}s",
        show_enter: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to measure and log execution time of a function.

    Args:
        logger: (optional) a bound logger to use.
        identifier: (optional) identifier to bind temporarily.
        level: log level for messages.
        enter_message: message to display before execution (if show_enter=True).
                      You can use {func} placeholder for function name.
        exit_message: message to display after execution with duration.
                      Supports placeholders: {func}, {duration:.3f}.
        show_enter: whether to log the enter_message at function entry.

    Returns:
        Callable[[Callable[P, R]], Callable[P, R]]: A decorator preserving the wrapped signature.

    Steps:
        # 1. Select an appropriate logger (respect `logger`, otherwise bind `identifier` or use global).
        # 2. On wrapper enter, optionally log the enter message.
        # 3. Measure runtime using a high-precision monotonic clock.
        # 4. Execute the function and capture the result.
        # 5. Log the exit message with the measured duration.
        # 6. Return the function's result.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # 1. Select an appropriate logger (respect `logger`, otherwise bind `identifier` or use global).
        log = (logger or _loguru_logger.bind(identifier=identifier)) if identifier else (logger or _loguru_logger)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # 2. On wrapper enter, optionally log the enter message.
            if show_enter and enter_message:
                log.opt(lazy=True).log(level, enter_message.format(func=func.__name__))

            # 3. Measure runtime using a high-precision monotonic clock.
            start: float = time.perf_counter()

            # 4. Execute the function and capture the result.
            result: R = func(*args, **kwargs)

            # 5. Log the exit message with the measured duration.
            duration: float = time.perf_counter() - start
            if exit_message:
                log.opt(lazy=True).log(level, exit_message.format(func=func.__name__, duration=duration))

            # 6. Return the function's result.
            return result

        return wrapper

    return decorator


def log_io(
        *,
        logger: Any | None = None,
        identifier: str | None = None,
        level: str = "DEBUG",
        log_args: bool = True,
        log_return: bool = True,
        message_args: str = "Calling {func} with args={args}, kwargs={kwargs}",
        message_return: str = "{func} returned {result!r}",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to log function arguments and/or return value.

    Args:
        logger: (optional) a bound logger to use.
        identifier: (optional) identifier to bind temporarily.
        level: log level for messages.
        log_args: whether to log arguments at call time.
        log_return: whether to log return value at exit.
        message_args: message template for arguments (supports {func}, {args}, {kwargs}).
        message_return: message template for return value (supports {func}, {result}).

    Returns:
        Callable[[Callable[P, R]], Callable[P, R]]: A decorator preserving the wrapped signature.

    Steps:
        # 1. Select an appropriate logger (respect `logger`, otherwise bind `identifier` or use global).
        # 2. On call, optionally log the function arguments.
        # 3. Execute the function and capture the result.
        # 4. On return, optionally log the result.
        # 5. Return the function's result.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # 1. Select an appropriate logger (respect `logger`, otherwise bind `identifier` or use global).
        log = (logger or _loguru_logger.bind(identifier=identifier)) if identifier else (logger or _loguru_logger)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # 2. On call, optionally log the function arguments.
            if log_args:
                log.opt(lazy=True).log(level, message_args.format(func=func.__name__, args=args, kwargs=kwargs))

            # 3. Execute the function and capture the result.
            result: R = func(*args, **kwargs)

            # 4. On return, optionally log the result.
            if log_return:
                log.opt(lazy=True).log(level, message_return.format(func=func.__name__, result=result))

            # 5. Return the function's result.
            return result

        return wrapper

    return decorator
