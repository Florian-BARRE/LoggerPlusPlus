# ====== Code Summary ======
# Opt-in one-call configuration of LoggerPlusPlus: a console sink (with a format chosen
# by name), an optional plain file sink, and optional stdlib-logging interception — plus
# an environment-driven variant so every service configures logging the same way instead
# of re-implementing the same bootstrap. Nothing here runs at import time.

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional, Union

from loguru import logger as _loguru_logger

from . import formats
from .api import add
from .intercept import intercept_std_logging

__all__: list[str] = ["setup", "configure_from_env"]

_TRUE = frozenset({"1", "true", "yes", "on"})


def _env_bool(value: str) -> bool:
    """Parse a boolean-ish environment string."""
    return value.strip().lower() in _TRUE


def _resolve_format(fmt: Any, colorized: bool) -> Any:
    """
    Resolve a format spec to something loguru accepts.

    A bare identifier is treated as a format NAME and instantiated from the shipped
    formats (an unknown name raises, rather than silently rendering the word literally).
    A string containing `{` is a raw loguru template. A format instance is itself a
    template (it subclasses `str`), and any other object (e.g. a callable) passes through.

    Raises:
        ValueError: If a bare-identifier name does not resolve to a shipped format.
    """
    if isinstance(fmt, str) and "{" not in fmt and fmt.isidentifier():
        cls = getattr(formats, fmt, None)
        if (
            isinstance(cls, type)
            and issubclass(cls, formats.BaseFormat)
            and cls is not formats.BaseFormat
        ):
            return cls(colorized=colorized)
        raise ValueError(
            f"unknown format name {fmt!r}; use a shipped format class name "
            "(e.g. 'ShortFormat') or a loguru template containing '{...}'"
        )
    return fmt


def setup(
    *,
    level: Union[int, str] = "DEBUG",
    format: Any = "DebugFormat",
    colorize: Optional[bool] = None,
    sink: Any = None,
    file: Optional[Any] = None,
    file_level: Optional[Union[int, str]] = None,
    file_format: Any = None,
    rotation: Optional[Any] = None,
    retention: Optional[Any] = None,
    enqueue: bool = False,
    intercept: bool = False,
    remove_default: bool = True,
    remove_existing: bool = False,
) -> Dict[str, int]:
    """
    Configure LoggerPlusPlus in one opt-in call (never invoked at import).

    Adds a console sink using a format resolved by name (the boilerplate every service
    otherwise repeats) and, optionally, a plain file sink and stdlib-logging interception.

    Args:
        level (int | str): Level for the console sink (default "DEBUG").
        format (Any): A shipped format name (e.g. "OpsFormat"), a raw loguru format string,
            or a format instance/callable. Names are resolved from `loggerplusplus.formats`.
        colorize (bool | None): loguru colorize for the console sink (None = auto by TTY).
        sink (Any): Console sink (default: sys.stderr).
        file (Any | None): Optional file path; when given, a second, plain (uncolored) sink.
        file_level (int | str | None): Level for the file sink (default: same as `level`).
        file_format (Any | None): Format for the file sink (default: same as `format`, plain).
        rotation / retention (Any | None): Forwarded to the file sink.
        enqueue (bool): Enqueue records (process-safe) on both sinks.
        intercept (bool): Also route the standard library `logging` through loguru.
        remove_default (bool): Remove loguru's default handler (its stderr sink) first, so
            it does not duplicate the console sink. Leaves any sinks the app already added
            untouched (default True).
        remove_existing (bool): Remove ALL existing sinks first — a full clean slate. This
            also drops sinks the application configured, so it is off by default.

    Returns:
        dict[str, int]: Sink ids, e.g. {"console": 1} or {"console": 1, "file": 2}.
    """
    # 1. Clear sinks: everything on request, otherwise just loguru's default handler (id 0).
    if remove_existing:
        _loguru_logger.remove()
    elif remove_default:
        try:
            _loguru_logger.remove(0)
        except ValueError:
            pass  # the default handler was already removed

    # 2. Console sink with the resolved (colorized-tag) format.
    console = sys.stderr if sink is None else sink
    sinks: Dict[str, int] = {
        "console": add(
            sink=console,
            level=level,
            format=_resolve_format(format, True),
            colorize=colorize,
            enqueue=enqueue,
        )
    }

    # 3. Optional plain file sink.
    if file is not None:
        sinks["file"] = add(
            sink=file,
            level=level if file_level is None else file_level,
            format=_resolve_format(
                format if file_format is None else file_format, False
            ),
            colorize=False,
            enqueue=enqueue,
            rotation=rotation,
            retention=retention,
        )

    # 4. Optionally bridge standard-library logging.
    if intercept:
        intercept_std_logging()

    return sinks


def configure_from_env(prefix: str = "LOGGING_LPP_") -> Dict[str, int]:
    """
    Configure logging from environment variables (a thin wrapper over `setup`).

    Reads `<prefix>LEVEL`, `<prefix>FORMAT`, `<prefix>COLORIZE`, `<prefix>FILE`,
    `<prefix>FILE_LEVEL`, `<prefix>ROTATION`, `<prefix>RETENTION`, `<prefix>ENQUEUE`,
    `<prefix>INTERCEPT`. Unset variables fall back to `setup`'s defaults.

    Args:
        prefix (str): Environment variable prefix (default "LOGGING_LPP_").

    Returns:
        dict[str, int]: The sink ids from `setup`.
    """
    env = os.environ
    kwargs: Dict[str, Any] = {}

    # 1. Level options: an all-digit string is a numeric level (env values are always
    #    strings, so coerce it to int; loguru rejects a numeric level given as a string).
    for env_key, arg in (("LEVEL", "level"), ("FILE_LEVEL", "file_level")):
        value = env.get(prefix + env_key)
        if value:
            kwargs[arg] = int(value) if value.isdigit() else value

    # 2. Other string-valued options (only override when non-empty).
    for env_key, arg in (
        ("FORMAT", "format"),
        ("FILE", "file"),
        ("ROTATION", "rotation"),
        ("RETENTION", "retention"),
    ):
        value = env.get(prefix + env_key)
        if value:
            kwargs[arg] = value

    # 3. Boolean-valued options (an empty string is ignored, keeping the default).
    for env_key, arg in (
        ("COLORIZE", "colorize"),
        ("ENQUEUE", "enqueue"),
        ("INTERCEPT", "intercept"),
    ):
        value = env.get(prefix + env_key)
        if value:
            kwargs[arg] = _env_bool(value)

    return setup(**kwargs)
