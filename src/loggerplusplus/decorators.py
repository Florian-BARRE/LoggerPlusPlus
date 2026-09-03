# ====== Code Summary ======
# Convenience decorators and wrappers around `loguru` that:
# - provide optional identifier binding (via `extra['identifier']`),
# - expose `catch` and `opt` helpers that respect a passed logger or identifier,
# - add decorators to log execution timing and I/O (arguments/return values).
# Designed to be drop-in friendly for operational and debugging use.

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import Any, Optional, TypeVar

from loguru import logger as _loguru_logger

__all__: list[str] = ["catch", "opt", "log_timing", "log_io"]

R = TypeVar("R")

# A logging hook: (log, func, args, kwargs[, result/state]) -> arbitrary carry state.
_Hook = Callable[..., Any]


def _select_logger(
    logger: Optional[Any] = None, identifier: Optional[str] = None
) -> Any:
    """
    Select an appropriate logger, optionally binding an identifier.

    Args:
        logger (Any | None): A pre-bound logger to use if provided (takes precedence).
        identifier (str | None): If provided and no `logger` is passed, bind this
            identifier to the global loguru logger.

    Returns:
        Any: A logger-like object (loguru `Logger` or bound proxy).
    """
    # 1. A provided logger wins; else bind the identifier if any; else the global logger.
    if logger is not None:
        return logger
    return _loguru_logger.bind(identifier=identifier) if identifier else _loguru_logger


def _make_decorator(
    logger: Optional[Any],
    identifier: Optional[str],
    on_enter: _Hook,
    on_exit: _Hook,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Build a decorator that selects a logger once, then runs `on_enter`/`on_exit`.

    Factoring this shell keeps `log_timing` and `log_io` from each copying the same
    logger-selection + `functools.wraps` scaffolding; they supply only their hooks.

    Args:
        logger (Any | None): Optional pre-bound logger (takes precedence).
        identifier (str | None): Optional identifier to bind when no logger is given.
        on_enter (_Hook): Called as `on_enter(log, func, args, kwargs)`; its return value
            is carried to `on_exit` as `state`.
        on_exit (_Hook): Called as `on_exit(log, func, args, kwargs, result, state)`.

    Returns:
        Callable[[Callable[..., R]], Callable[..., R]]: The decorator.
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        # 1. Resolve the effective logger once, at decoration time.
        log = _select_logger(logger=logger, identifier=identifier)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # 2. Enter hook (may carry state, e.g. a start timestamp), call, exit hook.
            state = on_enter(log, func, args, kwargs)
            result: R = func(*args, **kwargs)
            on_exit(log, func, args, kwargs, result, state)
            return result

        return wrapper

    return decorator


def catch(
    *decorator_args: Any,
    identifier: Optional[str] = None,
    logger: Optional[Any] = None,
    **decorator_kwargs: Any,
) -> Any:
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
    """
    # 1. Resolve the effective logger, then delegate to its `catch`.
    bound = _select_logger(logger=logger, identifier=identifier)
    return bound.catch(*decorator_args, **decorator_kwargs)


def opt(
    *args: Any,
    identifier: Optional[str] = None,
    logger: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
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
    """
    # 1. Resolve the effective logger, then delegate to its `opt`.
    bound = _select_logger(logger=logger, identifier=identifier)
    return bound.opt(*args, **kwargs)


def log_timing(
    *,
    logger: Optional[Any] = None,
    identifier: Optional[str] = None,
    level: str = "DEBUG",
    enter_message: Optional[str] = None,
    exit_message: str = "Finished {func} in {duration:.3f}s",
    show_enter: bool = True,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator to measure and log execution time of a function.

    Args:
        logger: (optional) a bound logger to use.
        identifier: (optional) identifier to bind temporarily.
        level: log level for messages.
        enter_message: message before execution (if show_enter=True); supports {func}.
        exit_message: message after execution; supports {func}, {duration:.3f}.
        show_enter: whether to log the enter_message at function entry.

    Returns:
        Callable[[Callable[..., R]], Callable[..., R]]: A decorator preserving the signature.
    """

    def on_enter(log: Any, func: Any, args: Any, kwargs: Any) -> float:
        # 1. Optionally log the enter message, then start the high-precision clock.
        if show_enter and enter_message:
            log.opt(lazy=True).log(level, enter_message.format(func=func.__name__))
        return time.perf_counter()

    def on_exit(
        log: Any, func: Any, args: Any, kwargs: Any, result: Any, start: float
    ) -> None:
        # 2. Log the exit message with the measured duration.
        if exit_message:
            duration: float = time.perf_counter() - start
            log.opt(lazy=True).log(
                level, exit_message.format(func=func.__name__, duration=duration)
            )

    return _make_decorator(logger, identifier, on_enter, on_exit)


def log_io(
    *,
    logger: Optional[Any] = None,
    identifier: Optional[str] = None,
    level: str = "DEBUG",
    log_args: bool = True,
    log_return: bool = True,
    message_args: str = "Calling {func} with args={args}, kwargs={kwargs}",
    message_return: str = "{func} returned {result!r}",
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator to log function arguments and/or return value.

    Args:
        logger: (optional) a bound logger to use.
        identifier: (optional) identifier to bind temporarily.
        level: log level for messages.
        log_args: whether to log arguments at call time.
        log_return: whether to log return value at exit.
        message_args: template for arguments (supports {func}, {args}, {kwargs}).
        message_return: template for return value (supports {func}, {result}).

    Returns:
        Callable[[Callable[..., R]], Callable[..., R]]: A decorator preserving the signature.
    """

    def on_enter(log: Any, func: Any, args: Any, kwargs: Any) -> None:
        # 1. Optionally log the call arguments.
        if log_args:
            log.opt(lazy=True).log(
                level,
                message_args.format(func=func.__name__, args=args, kwargs=kwargs),
            )

    def on_exit(
        log: Any, func: Any, args: Any, kwargs: Any, result: Any, state: Any
    ) -> None:
        # 2. Optionally log the return value.
        if log_return:
            log.opt(lazy=True).log(
                level, message_return.format(func=func.__name__, result=result)
            )

    return _make_decorator(logger, identifier, on_enter, on_exit)
