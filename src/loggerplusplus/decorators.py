# ====== Code Summary ======
# Convenience decorators and wrappers around `loguru` that:
# - provide optional identifier binding (via `extra['identifier']`),
# - expose `catch` and `opt` helpers that respect a passed logger or identifier,
# - add decorators to log execution timing and I/O (arguments/return values).
# Logging is emitted lazily and defensively: building a message (including argument
# reprs) happens only when the record will be emitted, and a logging failure can never
# propagate into — or abort — the decorated function.
# log_timing/log_io transparently support sync functions, `async def` coroutines, and
# async generators (only a real `async def`/`async def ... yield` gets the awaiting
# wrapper — a plain function that merely returns a coroutine cannot be detected).
# Control-flow BaseExceptions (cancellation, KeyboardInterrupt, ...) are re-raised without
# being logged as a failure.

from __future__ import annotations

import functools
import inspect
import time
from collections.abc import Callable, Iterable
from typing import Any, Optional, TypeVar

from loguru import logger as _loguru_logger

from .redact import (  # LEGACY-SEAM: re-home — remove in R-00 (Redact is permanent; the rest re-exports)
    SENSITIVE_KEYS,
    Redact,
    _redact_call,  # noqa: F401 - re-export seam consumed by tests/test_decorators_enriched.py
    _shorten,  # noqa: F401 - re-export seam consumed by tests/test_decorators_enriched.py
)

__all__: list[str] = ["catch", "opt", "log_timing", "log_io", "SENSITIVE_KEYS"]

R = TypeVar("R")

# A logging hook: (log, func, args, kwargs[, extra...]) -> arbitrary carry state.
_Hook = Callable[..., Any]


def _emit(log: Any, level: str, build: Callable[[], str]) -> None:
    """
    Emit a lazily-built message; a logging failure never reaches the caller.

    `build` (which formats the message and may `repr()` arguments) is passed to loguru
    lazily, so it runs only when the record will actually be emitted — a disabled level
    pays nothing. The whole call is guarded so a formatting error (e.g. an argument whose
    `__repr__` raises) can never propagate out of, or abort, the decorated function.

    Args:
        log (Any): The bound logger.
        level (str): The log level.
        build (Callable[[], str]): Zero-arg callable returning the final message.
    """
    try:
        log.opt(lazy=True).log(level, "{_m}", _m=build)
    except Exception:  # noqa: BLE001 - a logging failure must never abort the caller
        pass


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
    on_error: Optional[_Hook] = None,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Build a decorator that selects a logger once, then runs the enter/exit/error hooks.

    The decorated call is wrapped so `on_exit` runs on success and `on_error` (if given)
    runs on failure before the exception re-raises — so timing/telemetry is not lost when
    the function raises. Hooks emit through `_emit`, so they never abort the call.

    Args:
        logger (Any | None): Optional pre-bound logger (takes precedence).
        identifier (str | None): Optional identifier to bind when no logger is given.
        on_enter (_Hook): `on_enter(log, func, args, kwargs)`; its return is carried as `state`.
        on_exit (_Hook): `on_exit(log, func, args, kwargs, result, state)` on success.
        on_error (_Hook | None): `on_error(log, func, args, kwargs, exc, state)` on failure.

    Returns:
        Callable[[Callable[..., R]], Callable[..., R]]: The decorator.
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        # 1. Resolve the effective logger once, at decoration time.
        log = _select_logger(logger=logger, identifier=identifier)

        # 2. Async generators: wrap so timing spans the full consumption and errors raised
        #    while iterating still reach on_error (there is no single return value).
        if inspect.isasyncgenfunction(func):

            @functools.wraps(func)
            async def async_gen_wrapper(*args: Any, **kwargs: Any) -> Any:
                state = on_enter(log, func, args, kwargs)
                try:
                    async for item in func(*args, **kwargs):
                        yield item
                except BaseException as exc:
                    if on_error is not None and isinstance(exc, Exception):
                        on_error(log, func, args, kwargs, exc, state)
                    raise
                on_exit(log, func, args, kwargs, None, state)

            return async_gen_wrapper

        # 3. Coroutine functions need an awaiting wrapper so timing/return reflect the
        #    actual execution, not the creation of the coroutine object.
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                state = on_enter(log, func, args, kwargs)
                try:
                    result = await func(*args, **kwargs)
                except BaseException as exc:
                    if on_error is not None and isinstance(exc, Exception):
                        on_error(log, func, args, kwargs, exc, state)
                    raise
                on_exit(log, func, args, kwargs, result, state)
                return result

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # 4. Enter hook, then call; on a real error run on_error and re-raise, else
            #    on_exit. Control-flow BaseExceptions (cancellation, KeyboardInterrupt,
            #    SystemExit, GeneratorExit) propagate without being logged as a failure.
            state = on_enter(log, func, args, kwargs)
            try:
                result: R = func(*args, **kwargs)
            except BaseException as exc:
                if on_error is not None and isinstance(exc, Exception):
                    on_error(log, func, args, kwargs, exc, state)
                raise
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
    error_message: str = "Failed {func} after {duration:.3f}s: {error!r}",
    show_enter: bool = True,
    min_duration: Optional[float] = None,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator to measure and log execution time of a function.

    Args:
        logger: (optional) a bound logger to use.
        identifier: (optional) identifier to bind temporarily.
        level: log level for messages.
        enter_message: message before execution (if show_enter=True); supports {func}.
        exit_message: message after a successful call; supports {func}, {duration:.3f}.
        error_message: message when the call raises; supports {func}, {duration:.3f}, {error}.
            The exception is re-raised afterwards; set to "" to skip the failure log.
        show_enter: whether to log the enter_message at function entry.
        min_duration: if set, only log the exit message when the measured duration (in
            seconds) is at least this value — useful to surface only slow calls. Failures
            are always logged (via error_message) regardless of this threshold.

    Returns:
        Callable[[Callable[..., R]], Callable[..., R]]: A decorator preserving the signature.
    """

    def on_enter(log: Any, func: Any, args: Any, kwargs: Any) -> float:
        # 1. Optionally log the enter message, then start the high-precision clock.
        if show_enter and enter_message:
            _emit(log, level, lambda: enter_message.format(func=func.__name__))
        return time.perf_counter()

    def on_exit(
        log: Any, func: Any, args: Any, kwargs: Any, result: Any, start: float
    ) -> None:
        # 2. Log the exit message, honoring the optional slow-call threshold.
        duration = time.perf_counter() - start
        if exit_message and (min_duration is None or duration >= min_duration):
            _emit(
                log,
                level,
                lambda: exit_message.format(func=func.__name__, duration=duration),
            )

    def on_error(
        log: Any, func: Any, args: Any, kwargs: Any, exc: BaseException, start: float
    ) -> None:
        # 3. On failure, still emit the measured duration (the call you most want timed).
        duration = time.perf_counter() - start
        if error_message:
            _emit(
                log,
                level,
                lambda: error_message.format(
                    func=func.__name__, duration=duration, error=exc
                ),
            )

    return _make_decorator(logger, identifier, on_enter, on_exit, on_error)


def log_io(
    *,
    logger: Optional[Any] = None,
    identifier: Optional[str] = None,
    level: str = "DEBUG",
    log_args: bool = True,
    log_return: bool = True,
    message_args: str = "Calling {func} with args={args}, kwargs={kwargs}",
    message_return: str = "{func} returned {result!r}",
    redact: Iterable[str] = (),
    max_value_length: Optional[int] = None,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator to log function arguments and/or return value.

    On success both args and return are logged; if the function raises, only the args
    line (if enabled) has already been logged — there is no return line.

    Args:
        logger: (optional) a bound logger to use.
        identifier: (optional) identifier to bind temporarily.
        level: log level for messages.
        log_args: whether to log arguments at call time.
        log_return: whether to log return value at exit.
        message_args: template for arguments (supports {func}, {args}, {kwargs}).
        message_return: template for return value (supports {func}, {result}).
        redact: case-insensitive name substrings. Any argument — positional (matched via
            the signature) or keyword — whose parameter name matches has its value masked
            as "***"; dict values are masked recursively by key. Matching is substring, so
            a name merely containing a sensitive word is also masked. Pass `SENSITIVE_KEYS`
            for a sensible default. Does not recurse into arbitrary (non-dict) objects.
        max_value_length: if set, any argument/return whose repr exceeds this length is
            shortened (its truncated repr is logged instead of the full value).

    Returns:
        Callable[[Callable[..., R]], Callable[..., R]]: A decorator preserving the signature.
    """

    def on_enter(log: Any, func: Any, args: Any, kwargs: Any) -> None:
        # 1. Lazily build the (redacted, shortened) call message.
        if log_args:

            def build() -> str:
                shown_args, shown_kwargs = Redact.redact_call(
                    func, args, kwargs, redact
                )
                shown_args = Redact.shorten_args(shown_args, max_value_length)
                shown_kwargs = Redact.shorten_kwargs(shown_kwargs, max_value_length)
                return message_args.format(
                    func=func.__name__, args=shown_args, kwargs=shown_kwargs
                )

            _emit(log, level, build)

    def on_exit(
        log: Any, func: Any, args: Any, kwargs: Any, result: Any, state: Any
    ) -> None:
        # 2. Lazily build the (shortened) return message.
        if log_return:
            _emit(
                log,
                level,
                lambda: message_return.format(
                    func=func.__name__, result=Redact.shorten(result, max_value_length)
                ),
            )

    return _make_decorator(logger, identifier, on_enter, on_exit)
