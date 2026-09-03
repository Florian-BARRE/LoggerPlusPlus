# ====== Code Summary ======
# Wrapper utilities around the `loguru` logger providing custom format parsing
# and filter composition. Exposes a simplified API (`add`, `remove`, `enable`,
# `disable`, `bind`, `configure`) while extending format handling with
# project-specific enhancements.

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Optional, Union

from loguru import logger as _loguru_logger

from .parser import prepare_auto_format
from .runtime import compose_filter

# ------------------- Public API ------------------- #
__all__ = [
    "logger",
    "add",
]

# Re-export the base logger
logger = _loguru_logger


def add(
    sink: Any,
    *,
    level: Union[int, str] = "DEBUG",
    format: Union[str, Callable[[dict[str, Any]], str]] = "{time} {level} {message}",
    filter: Optional[Union[Callable[[dict[str, Any]], bool], Mapping[str, str]]] = None,
    colorize: Optional[bool] = None,
    serialize: bool = False,
    backtrace: bool = False,
    diagnose: bool = False,
    enqueue: bool = False,
    catch: bool = False,
    **kwargs: Any,
) -> int:
    """
    Add a new logging sink with optional custom formatting and filters.

    Args:
        sink (Any): The sink where logs should be written (file, stdout, etc.).
        level (int | str): Minimum logging level for this sink (default: "DEBUG").
        format (str | Callable): A string template or callable for message formatting.
        filter (Callable | Mapping | None): Filtering logic or mapping of modules to levels.
        colorize (bool | None): Whether to colorize output (default: None).
        serialize (bool): Whether to serialize logs as JSON (default: False).
        backtrace (bool): Whether to show detailed exception backtraces (default: False).
        diagnose (bool): Whether to enable extra debugging information (default: False).
        enqueue (bool): Whether to enqueue logs for multiprocessing (default: False).
        catch (bool): Whether to catch and handle sink errors (default: False).
        **kwargs (Any): Additional arguments forwarded to loguru's `add`.

    Returns:
        int: The identifier of the newly added sink.
    """
    # 1. Start from the caller's values (used as-is when the format is a callable).
    new_format = format
    new_filter = filter

    # 2. For string formats, rewrite auto-width tokens; if any were found, wrap the
    #    filter so widths are computed per record (see runtime.compose_filter).
    if isinstance(format, str):
        new_format, mappings = prepare_auto_format(format)
        if mappings:
            new_filter = compose_filter(filter, mappings)

    return _loguru_logger.add(
        sink,
        level=level,
        format=new_format,
        filter=new_filter,
        colorize=colorize,
        serialize=serialize,
        backtrace=backtrace,
        diagnose=diagnose,
        enqueue=enqueue,
        catch=catch,
        **kwargs,
    )
