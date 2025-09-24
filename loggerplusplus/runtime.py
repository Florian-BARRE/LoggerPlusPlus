# ====== Code Summary ======
# Compose a runtime filter callable that pre-computes dynamic "auto-width"
# placeholders for log records before delegating to a user-provided filter.
# Integrates with the auto-width registry to maintain aligned fields.

from __future__ import annotations

# ====== Standard Library Imports ======
import re  # (used in type annotations for re.Match in helpers' docstrings)

# ====== Third-Party Library Imports ======
# (No third-party imports required)

# ====== Internal Project Imports ======
# (No internal absolute imports required)

# ====== Local Project Imports ======
from typing import Any, Final
from collections.abc import Callable
from .registry import _AUTO

__all__: list[str] = ["compose_filter"]

# Runtime mapping metadata structure:
# Mapping: (field, placeholder_key, align, width_spec, cap, trunc)
_AutoMap = tuple[str, str, str, str, int | None, str | None]

# Convenience type for loguru-like records
_Record = dict[str, Any]


def compose_filter(
        user_filter: Callable[[dict], bool] | dict[str, str] | None,
        auto_mappings: list[_AutoMap],
) -> Callable[[dict], bool]:
    """
    Build a filter that computes dynamic placeholders and then applies user's filter.

    This wrapper returns a callable compatible with Loguru's `filter` parameter.
    It precomputes `extra[__lp_auto_i__]` values using `auto_mappings` and the
    auto-width registry, then evaluates the original `user_filter` when provided.

    Notes:
        - If `user_filter` is a mapping (dict), this function replicates the original
          behavior and always returns `True` (i.e., does not apply mapping-based
          filtering here). The mapping is expected to be handled elsewhere by Loguru.
        - Width logic:
            * `width_spec == "auto"` uses the `_AUTO` registry's observed maximum.
            * `cap` limits the width (and truncation) when provided.
            * `trunc` (left/right/middle) determines how overlong text is shortened.
            * Without `trunc`, precision formatting (`.{width}`) hard-cuts the text.

    Args:
        user_filter (Callable[[dict], bool] | dict[str, str] | None): Optional upstream filter.
        auto_mappings (list[_AutoMap]): Parsed mappings describing dynamic fields.

    Returns:
        Callable[[dict], bool]: A filter to be passed to Loguru.
    """

    def _getattr_path(container: Any, path: str) -> Any:
        """
        Resolve a dotted attribute path through dict-like and attribute access.

        Args:
            container (Any): The object or dict to navigate.
            path (str): Dotted path (e.g., "level.name" or "extra[service]").

        Returns:
            Any: The resolved value or None if not found.
        """
        # 1. Initialize traversal state
        cur: Any = container

        # 2. Traverse each dotted component
        for part in path.split("."):
            if cur is None:
                return None
            # 2.1. Dict key access
            if isinstance(cur, dict) and part in cur:
                cur = cur.get(part)
                continue
            # 2.2. Attribute access
            if hasattr(cur, part):
                cur = getattr(cur, part)
                continue
            # 2.3. Unresolvable step
            return None

        # 3. Return the final resolved object
        return cur

    def resolve(record: _Record, field_spec: str) -> Any:
        """
        Resolve a field specification against the log record, honoring `extra[...]`.

        Args:
            record (_Record): The log record dict provided by Loguru.
            field_spec (str): Field spec (e.g., "extra[service]", "level.name").

        Returns:
            Any: The resolved value or None.
        """
        # 1. Handle explicit extra[...] lookup
        if field_spec.startswith("extra[") and field_spec.endswith("]"):
            key = field_spec[6:-1]
            return record["extra"].get(key)

        # 2. Try dotted-path resolution over the record
        val = _getattr_path(record, field_spec)
        if val is not None:
            return val

        # 3. Fallback to record["extra"][field_spec]
        return record["extra"].get(field_spec)

    def _truncate(value: str, width: int, mode: str) -> str:
        """
        Truncate `value` to `width` using the specified mode.

        Args:
            value (str): Source string.
            width (int): Target width (>= 0).
            mode (str): One of {"left", "right", "middle"}.

        Returns:
            str: Truncated string respecting the mode and width.
        """
        # 1. No truncation needed
        if len(value) <= width:
            return value

        # 2. Degenerate width cases
        if width <= 1:
            return value[:width]

        # 3. Apply mode-specific truncation using ellipsis
        if mode == "right":
            return value[: max(0, width - 1)] + "…"
        if mode == "left":
            return "…" + value[-(width - 1):]
        if mode == "middle":
            left = (width - 1) // 2
            right = width - 1 - left
            return value[:left] + "…" + value[-right:]

        # 4. Fallback hard cut
        return value[:width]

    def built_filter(record: _Record) -> bool:
        """
        Compute dynamic placeholders, then apply the user-provided filter if callable.

        Args:
            record (_Record): Loguru record provided to filter.

        Returns:
            bool: Whether the record should pass the filter.
        """
        # 1. For each auto-mapping, resolve, size, and pad the placeholder value
        for field_spec, placeholder_key, align, width_spec, cap, trunc in auto_mappings:
            # 1.1. Resolve source value and normalize to text with "-" sentinel
            raw: Any = resolve(record, field_spec)
            text: str = "-" if raw is None else str(raw)

            # 1.2. Determine final width (auto observed vs. fixed, then capped)
            if width_spec == "auto":
                _AUTO.observe(field_spec, text)
                observed: int = _AUTO.width(field_spec)
                width: int = min(observed, cap) if cap is not None else observed
            else:
                width = max(1, int(width_spec))
                if cap is not None:
                    width = min(width, cap)

            # 1.3. Truncate (if requested) before padding to avoid overflow
            if trunc:
                to_pad: str = _truncate(text, width, trunc)
                if align == ">":
                    padded = f"{to_pad:>{width}}"
                elif align == "^":
                    padded = f"{to_pad:^{width}}"
                else:
                    padded = f"{to_pad:<{width}}"
            else:
                # 1.4. Use precision to hard-cut and align when no truncation mode set
                if align == ">":
                    padded = f"{text:>{width}.{width}}"
                elif align == "^":
                    padded = f"{text:^{width}.{width}}"
                else:
                    padded = f"{text:<{width}.{width}}"

            # 1.5. Attach computed placeholder into record.extra
            record["extra"][placeholder_key] = padded

        # 2. Evaluate the user-provided filter
        if user_filter is None:
            return True
        if callable(user_filter):
            return bool(user_filter(record))

        # 3. Original behavior: when mapping is provided, return True here
        return True

    # 4. Return the composed filter callable
    return built_filter
