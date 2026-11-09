# ====== Code Summary ======
# The redaction / truncation brick for `log_io`: a self-contained cluster of helpers that mask
# sensitive argument values (by parameter name, recursively into dict values) and shorten over-long
# values' reprs before they are logged. `SENSITIVE_KEYS` (a default set of case-insensitive
# substrings) lives here as its single source of truth. The helpers are plain module-level
# functions; `Redact` is a thin tool class whose staticmethods ARE those same functions, so
# `Redact.redact_call is _redact_call` and both spellings expose identical behaviour.

from __future__ import annotations

import inspect
from collections.abc import Iterable
from typing import Any, Dict, Optional, Tuple

# Default case-insensitive substrings marking an argument as sensitive; pass this
# (or your own list) as `log_io(redact=...)` to mask matching values in the logged call.
SENSITIVE_KEYS: Tuple[str, ...] = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "private_key",
)
_REDACTED: str = "***"


def _is_sensitive(name: str, patterns: Tuple[str, ...]) -> bool:
    """Return True when `name` contains any (case-insensitive) sensitive substring."""
    lowered = name.lower()
    return any(p.lower() in lowered for p in patterns)


def _deep_redact(value: Any, patterns: Tuple[str, ...]) -> Any:
    """Recurse into dict values, masking those whose key matches a sensitive pattern."""
    if isinstance(value, dict):
        return {
            k: (
                _REDACTED
                if _is_sensitive(str(k), patterns)
                else _deep_redact(v, patterns)
            )
            for k, v in value.items()
        }
    return value


def _redact_call(
    func: Any,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    patterns: Iterable[str],
) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    """
    Mask sensitive arguments by parameter name (positional and keyword) and in nested dicts.

    Positional arguments are matched to their parameter name via the function signature, so
    a secret passed positionally is masked too. Matching is case-insensitive substring;
    recursion covers dict values but not arbitrary objects.

    Args:
        func (Any): The decorated function (for its signature).
        args (tuple): Positional call arguments.
        kwargs (dict): Keyword call arguments.
        patterns (Iterable[str]): Sensitive name substrings.

    Returns:
        tuple: (shown_args, shown_kwargs) with sensitive values replaced by "***".
    """
    pats = tuple(patterns)
    if not pats:
        return args, kwargs
    try:
        names = list(inspect.signature(func).parameters)
    except (TypeError, ValueError):  # builtins / signature-less callables
        names = []
    shown_args = tuple(
        (
            _REDACTED
            if (i < len(names) and _is_sensitive(names[i], pats))
            else _deep_redact(a, pats)
        )
        for i, a in enumerate(args)
    )
    shown_kwargs = {
        k: (_REDACTED if _is_sensitive(k, pats) else _deep_redact(v, pats))
        for k, v in kwargs.items()
    }
    return shown_args, shown_kwargs


def _shorten(value: Any, max_len: Optional[int]) -> Any:
    """
    Return `value` unchanged, or a truncated repr string when its repr exceeds max_len.

    The returned truncated string is at most `max_len` characters (ellipsis included).
    """
    if max_len is None:
        return value
    text = repr(value)
    if len(text) <= max_len:
        return value
    if max_len <= 1:
        return "…"
    return text[: max_len - 1] + "…"


def _shorten_args(args: Tuple[Any, ...], max_len: Optional[int]) -> Tuple[Any, ...]:
    """Truncate each positional argument's repr to max_len (no-op when None)."""
    if max_len is None:
        return args
    return tuple(_shorten(a, max_len) for a in args)


def _shorten_kwargs(kwargs: Dict[str, Any], max_len: Optional[int]) -> Dict[str, Any]:
    """Truncate each keyword argument's repr to max_len (no-op when None)."""
    if max_len is None:
        return kwargs
    return {k: _shorten(v, max_len) for k, v in kwargs.items()}


class Redact:
    """
    The redaction / truncation toolkit for `log_io`.

    A pure tool class: every member is a `staticmethod` that is the same object as a module-level
    helper defined above (no instance state, no `__init__`). `Redact.redact_call is _redact_call`,
    `Redact.shorten is _shorten`, and so on — the class and the module functions are the same
    objects, so there is no duplicated logic.
    """

    is_sensitive = staticmethod(_is_sensitive)
    deep_redact = staticmethod(_deep_redact)
    redact_call = staticmethod(_redact_call)
    shorten = staticmethod(_shorten)
    shorten_args = staticmethod(_shorten_args)
    shorten_kwargs = staticmethod(_shorten_kwargs)
