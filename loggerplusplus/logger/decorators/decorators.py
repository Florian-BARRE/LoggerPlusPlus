# ====== Code Summary ======
# This module provides decorators for logging function calls, execution time,
# and tracing. It defines `log_calls`, `log_time`, and `trace`, which wrap
# functions to log entry, exit, duration, return values, and errors, with
# configurable logging behavior.

# ====== Standard Library Imports ======
import inspect
import logging
import time
from typing import Any, Callable

# ====== Local Project Imports ======
from .params import extract_param_meta
from .formatting import format_args, _safe_repr, _SENSITIVE_DEFAULT
from .wrappers import wrap_function


def _resolve_logger(
        logger: logging.Logger | None,
        identifier: str,
        func: Callable[..., Any],
) -> logging.Logger:
    """
    Resolve the logger to use for logging function activity.

    Args:
        logger (logging.Logger | None): Provided logger, if any.
        identifier (str | None): Optional identifier to override logger name.
        func (Callable): The target function.

    Returns:
        logging.Logger: The logger instance to use.
    """
    if logger is not None:
        return logger
    name = identifier if identifier else f"{func.__module__}"
    return logging.getLogger(name)


def log_calls(
        *,
        logger: logging.Logger | None = None,
        identifier: str | None = None,
        level: int = logging.DEBUG,
        level_on_error: int = logging.ERROR,
        include_args: bool = True,
        include_return: bool = False,
        max_repr_len: int = 200,
        sensitive_keys: set[str] = _SENSITIVE_DEFAULT,
        msg_prefix: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for logging function entry, exit, return values, and errors.

    Args:
        logger (logging.Logger | None): Logger instance, or resolved automatically.
        identifier (str | None): Optional identifier for log messages.
        level (int): Log level for normal events.
        level_on_error (int): Log level for errors.
        include_args (bool): Whether to log function arguments.
        include_return (bool): Whether to log return values.
        max_repr_len (int): Maximum length of repr() for arguments/returns.
        sensitive_keys (Iterable[str]): Keys to mask in argument logging.
        msg_prefix (str): Optional message prefix.

    Returns:
        Callable: A decorator wrapping the function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        log = _resolve_logger(logger, identifier, func)
        sig = inspect.signature(func)
        per_param = {
            name: extract_param_meta(p.default)
            for name, p in sig.parameters.items()
            if extract_param_meta(p.default)
        }

        def before_call(args, kwargs):
            # 1. Skip if logging is disabled at this level
            if not log.isEnabledFor(level):
                return

            # 2. Format function arguments
            try:
                bound = sig.bind_partial(*args, **kwargs)
                bound.apply_defaults()
                arg_str = format_args(
                    bound,
                    max_repr_len=max_repr_len,
                    sensitive_keys=sensitive_keys,
                    per_param=per_param,
                )
            except Exception:
                arg_str = "…"

            # 3. Log entry message
            msg = (
                f"{msg_prefix}→ {func.__qualname__}({arg_str})"
                if include_args
                else f"{msg_prefix}→ {func.__qualname__}"
            )
            log.log(
                level,
                msg,
                extra={"identifier": identifier} if identifier else None,
                stacklevel=3,
            )

        def after_call(result, args, kwargs):
            # 4. Log return value if enabled
            if include_return and log.isEnabledFor(level):
                log.log(
                    level,
                    f"{msg_prefix}← {func.__qualname__} returned {_safe_repr(result, max_repr_len)}",
                    extra={"identifier": identifier} if identifier else None,
                    stacklevel=3,
                )

        def on_error(e, args, kwargs):
            # 5. Log exceptions with traceback
            if log.isEnabledFor(level_on_error):
                log.log(
                    level_on_error,
                    f"{msg_prefix}✖ {func.__qualname__} raised {e.__class__.__name__}: {e}",
                    extra={"identifier": identifier} if identifier else None,
                    stacklevel=3,
                    exc_info=True,
                )

        return wrap_function(func, before_call, after_call, on_error)

    return decorator


def log_time(
        *,
        logger: logging.Logger | None = None,
        identifier: str | None = None,
        level: int = logging.DEBUG,
        level_over_threshold: int = logging.WARNING,
        threshold_ms: float = 0.0,
        include_args: bool = False,
        max_repr_len: int = 200,
        sensitive_keys: set[str] = _SENSITIVE_DEFAULT,
        msg_prefix: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for logging function execution time and detecting slow calls.

    Args:
        logger (logging.Logger | None): Logger instance, or resolved automatically.
        identifier (str | None): Optional identifier for log messages.
        level (int): Log level for normal timing messages.
        level_over_threshold (int): Log level if execution exceeds threshold.
        threshold_ms (float): Time threshold in milliseconds.
        include_args (bool): Whether to log function arguments on start.
        max_repr_len (int): Maximum length of repr() for arguments.
        sensitive_keys (Iterable[str]): Keys to mask in argument logging.
        msg_prefix (str): Optional message prefix.

    Returns:
        Callable: A decorator wrapping the function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        log = _resolve_logger(logger, identifier, func)
        sig = inspect.signature(func)

        def before_call(args, kwargs):
            # 1. Skip if logging is disabled
            if not log.isEnabledFor(level):
                return

            # 2. Log start message (with or without arguments)
            if not include_args:
                msg = f"{msg_prefix}⏱ {func.__qualname__} started"
            else:
                try:
                    bound = sig.bind_partial(*args, **kwargs)
                    bound.apply_defaults()
                    arg_str = format_args(
                        bound,
                        max_repr_len=max_repr_len,
                        sensitive_keys=sensitive_keys,
                    )
                except Exception:
                    arg_str = "…"
                msg = f"{msg_prefix}⏱ {func.__qualname__}({arg_str}) started"

            log.log(
                level,
                msg,
                extra={"identifier": identifier} if identifier else None,
                stacklevel=3,
            )
            setattr(func, "__lpp_start__", time.perf_counter())

        def after_call(result, args, kwargs):
            # 3. Compute execution duration
            t0 = getattr(func, "__lpp_start__", None)
            if t0 is None:
                return
            ms = (time.perf_counter() - t0) * 1000.0
            lvl = level_over_threshold if threshold_ms and ms >= threshold_ms else level

            # 4. Log completion message
            log.log(
                lvl,
                f"{msg_prefix}⏱ {func.__qualname__} finished in {ms:.2f} ms",
                extra={"identifier": identifier} if identifier else None,
                stacklevel=3,
            )

        def on_error(e, args, kwargs):
            # 5. Compute elapsed time and log failure
            t0 = getattr(func, "__lpp_start__", None)
            ms = (time.perf_counter() - t0) * 1000.0 if t0 else 0.0
            lvl = level_over_threshold if threshold_ms and ms >= threshold_ms else level
            log.log(
                lvl,
                f"{msg_prefix}✖ {func.__qualname__} failed in {ms:.2f} ms",
                extra={"identifier": identifier} if identifier else None,
                stacklevel=3,
                exc_info=True,
            )

        return wrap_function(func, before_call, after_call, on_error)

    return decorator


def trace(
        *,
        logger: logging.Logger | None = None,
        identifier: str | None = None,
        level: int = logging.DEBUG,
        level_on_error: int = logging.ERROR,
        level_over_threshold: int = logging.WARNING,
        threshold_ms: float = 0.0,
        include_args: bool = True,
        include_return: bool = False,
        max_repr_len: int = 200,
        sensitive_keys: set[str] = _SENSITIVE_DEFAULT,
        msg_prefix: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that combines both `log_calls` and `log_time`, tracing
    function entry, exit, execution duration, return values, and errors.

    Args:
        logger (logging.Logger | None): Logger instance, or resolved automatically.
        identifier (str | None): Optional identifier for log messages.
        level (int): Log level for normal events.
        level_on_error (int): Log level for errors.
        level_over_threshold (int): Log level if execution exceeds threshold.
        threshold_ms (float): Time threshold in milliseconds.
        include_args (bool): Whether to log function arguments.
        include_return (bool): Whether to log return values.
        max_repr_len (int): Maximum length of repr() for arguments/returns.
        sensitive_keys (Iterable[str]): Keys to mask in argument logging.
        msg_prefix (str): Optional message prefix.

    Returns:
        Callable: A decorator wrapping the function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return log_time(
            logger=logger,
            identifier=identifier,
            level=level,
            level_over_threshold=level_over_threshold,
            threshold_ms=threshold_ms,
            include_args=False,
            max_repr_len=max_repr_len,
            sensitive_keys=sensitive_keys,
            msg_prefix=msg_prefix,
        )(
            log_calls(
                logger=logger,
                identifier=identifier,
                level=level,
                level_on_error=level_on_error,
                include_args=include_args,
                include_return=include_return,
                max_repr_len=max_repr_len,
                sensitive_keys=sensitive_keys,
                msg_prefix=msg_prefix,
            )(func)
        )

    return decorator
