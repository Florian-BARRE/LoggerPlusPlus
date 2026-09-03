# ====== Code Summary ======
# Correlation context helpers: bind fields (a correlation id, a request id, arbitrary
# key/values) onto every log record emitted within a block, so a request can be traced
# across a service. Built on loguru's contextvars-based `contextualize`, so it is correct
# under threads and asyncio. OpenTelemetry trace/span ids are injected only when the
# (optional) opentelemetry package is importable — never a hard dependency.

from __future__ import annotations

import uuid
from typing import Any, ContextManager, Dict, Optional

from loguru import logger as _loguru_logger

__all__: list[str] = ["bind_context", "new_id", "otel_context"]


def new_id(prefix: str = "", *, length: int = 12) -> str:
    """
    Generate a short, unique correlation id.

    Args:
        prefix (str): Optional prefix (e.g. "req-").
        length (int): Number of hex characters from a uuid4 (default 12).

    Returns:
        str: The id, e.g. "req-3f9a1c2b4d5e".
    """
    token = uuid.uuid4().hex[:length]
    return f"{prefix}{token}" if prefix else token


def otel_context() -> Dict[str, str]:
    """
    Return the current OpenTelemetry trace/span ids, if OpenTelemetry is available.

    Returns:
        dict[str, str]: `{"trace_id": ..., "span_id": ...}` for a valid current span,
            otherwise an empty dict (opentelemetry not installed, or no active span).
    """
    # Guard the whole read: a missing OR broken/partial opentelemetry means "no context".
    try:
        from opentelemetry import trace  # optional, never a hard dependency

        ctx = trace.get_current_span().get_span_context()
        if not getattr(ctx, "is_valid", False):
            return {}
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
        }
    except Exception:
        return {}


def bind_context(
    *,
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    otel: bool = False,
    **fields: Any,
) -> ContextManager[None]:
    """
    Bind correlation fields onto every record emitted within the `with` block.

    Uses loguru's `contextualize`, so the bound fields land in each record's `extra` and
    are correctly scoped across threads and asyncio tasks. Any format or JSON sink that
    references `extra[...]` will then carry them.

    Args:
        correlation_id (str | None): A correlation id to bind as `extra["correlation_id"]`.
        request_id (str | None): A request id to bind as `extra["request_id"]`.
        otel (bool): Also inject the current OpenTelemetry `trace_id`/`span_id` when available.
        **fields (Any): Any additional key/values to bind.

    Returns:
        ContextManager[None]: A context manager scoping the bound fields.
    """
    # 1. Assemble the context, dropping unset ids.
    context: Dict[str, Any] = dict(fields)
    if correlation_id is not None:
        context["correlation_id"] = correlation_id
    if request_id is not None:
        context["request_id"] = request_id
    if otel:
        context.update(otel_context())

    # 2. Delegate to loguru's contextvars-based contextualize.
    return _loguru_logger.contextualize(**context)
