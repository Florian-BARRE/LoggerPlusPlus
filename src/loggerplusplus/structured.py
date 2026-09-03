# ====== Code Summary ======
# Structured (JSON) logging: add_json() installs a loguru sink that emits one compact
# JSON object per record (newline-delimited), with a clean, controllable field set that
# includes the identifier and user `extra`. It reuses loguru's own sink handling (files,
# rotation, enqueue) by injecting the serialized payload through the format callable.

from __future__ import annotations

import json
import traceback
from typing import Any, Dict, Iterable, Optional

from loguru import logger as _loguru_logger

__all__: list[str] = ["add_json"]

# Extra keys that are internal machinery and must never leak into the JSON payload.
_INTERNAL_PREFIXES = ("__lp_auto_", "_lpp_")


def _format_exception(exc: Any) -> Dict[str, Any]:
    """Serialize a loguru record exception (type, value, traceback) to a JSON-safe dict."""
    return {
        "type": exc.type.__name__ if exc.type else None,
        "value": str(exc.value) if exc.value else None,
        "traceback": (
            "".join(traceback.format_exception(exc.type, exc.value, exc.traceback))
            if exc.traceback is not None
            else None
        ),
    }


def _payload(record: Dict[str, Any], fields: Optional[Iterable[str]]) -> Dict[str, Any]:
    """
    Build the JSON payload for a loguru record.

    Args:
        record (dict): The loguru record.
        fields (Iterable[str] | None): If given, keep only these top-level keys.

    Returns:
        dict: The serializable payload.
    """
    exc = record["exception"]
    data: Dict[str, Any] = {
        "time": record["time"].isoformat(),
        "level": record["level"].name,
        "identifier": record["extra"].get("identifier"),
        "message": record["message"],
        "name": record["name"],
        "function": record["function"],
        "line": record["line"],
        "module": record["module"],
        "process": record["process"].id,
        "thread": record["thread"].id,
        "extra": {
            k: v
            for k, v in record["extra"].items()
            if k != "identifier" and not k.startswith(_INTERNAL_PREFIXES)
        },
        "exception": _format_exception(exc) if exc else None,
    }
    if fields is not None:
        wanted = tuple(fields)
        data = {k: data[k] for k in wanted if k in data}
    return data


def add_json(
    sink: Any,
    *,
    level: Any = "DEBUG",
    fields: Optional[Iterable[str]] = None,
    ensure_ascii: bool = False,
    **kwargs: Any,
) -> int:
    """
    Add a sink that emits one JSON object per record (newline-delimited).

    The payload includes time, level, identifier, message, source name/function/line/module,
    process/thread ids, the user `extra` (minus internal keys), and a structured `exception`.
    Suitable for log pipelines (ELK, Loki, Datadog, ...). Loguru manages the destination, so
    `sink` may be a stream, a callable, or a file path, and file rotation/retention/enqueue
    all work via the usual keyword arguments.

    Args:
        sink (Any): Any loguru sink (stream, callable, or file path).
        level (int | str): Minimum level (default "DEBUG").
        fields (Iterable[str] | None): Restrict the payload to these top-level keys.
        ensure_ascii (bool): Passed to json.dumps (default False keeps non-ASCII readable).
        **kwargs (Any): Forwarded to loguru's add (rotation, retention, enqueue, filter, ...).

    Returns:
        int: The id of the added sink.
    """

    def _json_format(record: Dict[str, Any]) -> str:
        # 1. Serialize into a private extra key, then return a template referencing it.
        #    (loguru substitutes the value verbatim; braces inside the JSON stay literal.)
        record["extra"]["_lpp_json"] = json.dumps(
            _payload(record, fields), default=str, ensure_ascii=ensure_ascii
        )
        return "{extra[_lpp_json]}"

    # 2. Never colorize JSON (a '<' in a string value would break loguru markup parsing).
    return _loguru_logger.add(
        sink, level=level, format=_json_format, colorize=False, **kwargs
    )
