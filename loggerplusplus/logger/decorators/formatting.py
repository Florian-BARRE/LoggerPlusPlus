# ====== Code Summary ======
# This module provides utilities for safe and consistent string representations
# of function arguments and values for logging. It includes masking of sensitive
# data, truncation of long representations, and argument formatting helpers.

# ====== Standard Library Imports ======
import inspect
from typing import Any

# Default set of sensitive keys to mask in logs
_SENSITIVE_DEFAULT: set[str] = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "auth",
    "apikey",
    "api_key",
    "authorization",
}


def _safe_repr(val: Any, max_len: int = 200) -> str:
    """
    Safely get the string representation of a value, with truncation.

    Args:
        val (Any): The value to represent.
        max_len (int): Maximum length of the representation before truncation.

    Returns:
        str: A safe, possibly truncated, string representation.
    """
    try:
        s = repr(val)
    except Exception:
        s = f"<unrepr {type(val).__name__}>"

    if len(s) > max_len:
        s = s[: max_len - 1] + "…"
    return s


def _mask(name: str, value: Any, sensitive: set[str]) -> Any:
    """
    Mask a value if its name indicates it is sensitive.

    Args:
        name (str): The parameter name.
        value (Any): The parameter value.
        sensitive (set[str]): Set of sensitive key substrings.

    Returns:
        Any: Masked value (`"***"`) if sensitive, otherwise original value.
    """
    lowered = name.lower()
    for key in sensitive:
        if key in lowered:
            return "***"
    return value


def format_args(
        bound: inspect.BoundArguments,
        *,
        max_repr_len: int = 200,
        sensitive_keys: set[str] = _SENSITIVE_DEFAULT,
        per_param: dict[str, Any] | None = None,
) -> str:
    """
    Format function arguments for logging, applying masking and safe repr.

    Args:
        bound (inspect.BoundArguments): Bound arguments from a function signature.
        max_repr_len (int): Maximum length of repr() output for arguments.
        sensitive_keys (set[str]): Keys considered sensitive and masked automatically.
        per_param (dict[str, Any] | None): Per-parameter metadata, may specify
            sensitivity or custom repr length.

    Returns:
        str: A comma-separated string of formatted arguments.
    """
    parts: list[str] = []
    per_param = per_param or {}

    # 1. Iterate through arguments
    for name, val in bound.arguments.items():
        m = per_param.get(name)

        # 2. Apply per-param sensitivity rules
        if m and getattr(m, "sensitive", False):
            val = "***"
        else:
            val = _mask(name, val, sensitive_keys)

        # 3. Apply repr length rules
        eff_len = (
            m.max_repr_len if (m and getattr(m, "max_repr_len", None) is not None) else max_repr_len
        )
        parts.append(f"{name}={_safe_repr(val, eff_len)}")

    return ", ".join(parts)
