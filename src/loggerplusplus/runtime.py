# ====== Code Summary ======
# Compose a runtime filter callable that pre-computes dynamic "auto-width"
# placeholders for log records before delegating to a user-provided filter.
# Integrates with the auto-width registry to maintain aligned fields.

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Optional, Union

from loguru import logger as _loguru_logger

from .parser import _AutoMap
from .registry import _AUTO

__all__: list[str] = ["compose_filter"]

# Convenience type for loguru-like records.
_Record = dict[str, Any]


def _apply_align(value: str, align: str, width: int, *, precision: bool = False) -> str:
    """
    Pad (and optionally hard-cut) `value` to `width` for the given alignment.

    Args:
        value (str): The text to align.
        align (str): One of ">", "^", "<" (anything else falls back to left).
        width (int): Target field width.
        precision (bool): When True, also hard-cut to `width` via format precision
            (used only when no truncation mode was requested on the token).

    Returns:
        str: The aligned string.
    """
    # 1. Map our align glyph to a Python format-spec alignment (default left)
    conv: str = ">" if align == ">" else ("^" if align == "^" else "<")

    # 2. Build the spec once and format (precision adds the `.{width}` hard cut)
    spec: str = f"{conv}{width}.{width}" if precision else f"{conv}{width}"
    return format(value, spec)


def _build_dict_filter(
    mapping: Mapping[Any, Any],
) -> Callable[[_Record], bool]:
    """
    Reproduce loguru's own dict-`filter` semantics as a callable.

    A dict filter maps a module name (or "" / None for the root) to a minimum level;
    the most specific matching prefix of `record["name"]` wins, `False` disables a module,
    and `True` maps to level 0. We must replicate this here because when an auto-width token
    is present the user's filter is wrapped (loguru never sees the original dict), so a dict
    filter would otherwise be silently ignored.

    Args:
        mapping (Mapping[str | None, Any]): The user-supplied dict filter.

    Returns:
        Callable[[_Record], bool]: A predicate applying loguru's level-per-module rules.
    """
    # 1. Resolve each configured value to a comparable level number (or False to disable)
    level_per_module: dict[str, Union[int, bool]] = {}
    for module, level in mapping.items():
        key = "" if module is None else module
        if level is False:
            level_per_module[key] = False
        elif level is True:
            level_per_module[key] = 0
        elif isinstance(level, str):
            level_per_module[key] = _loguru_logger.level(level).no
        elif isinstance(level, int):
            level_per_module[key] = level
        else:  # pragma: no cover - defensive: loguru rejects other types too
            raise TypeError(
                f"Invalid level value for module {module!r} in filter dict: {level!r}"
            )

    def _dict_filter(record: _Record) -> bool:
        # 2. Walk from the record's module up its dotted parents, most specific first
        name: str = record.get("name") or ""
        while True:
            level = level_per_module.get(name)
            if level is False:
                return False
            if level is not None:
                return bool(record["level"].no >= level)
            if not name:
                return True
            index = name.rfind(".")
            name = name[:index] if index != -1 else ""

    return _dict_filter


def compose_filter(
    user_filter: Optional[Union[Callable[[dict], bool], Mapping[str, Any]]],
    auto_mappings: list[_AutoMap],
) -> Callable[[dict], bool]:
    """
    Build a filter that computes dynamic placeholders and then applies user's filter.

    This wrapper returns a callable compatible with Loguru's `filter` parameter.
    It precomputes `extra[__lp_auto_i__]` values using `auto_mappings` and the
    auto-width registry, then evaluates the original `user_filter` when provided.

    The width math lives here, in a loguru *filter*, because loguru calls the filter
    exactly once per record BEFORE formatting — the only injection point where the padded
    / truncated string can be computed and written into `record["extra"]`.

    Args:
        user_filter (Callable[[dict], bool] | Mapping | None): Optional upstream filter.
            A callable is delegated to; a dict is applied with loguru's own semantics.
        auto_mappings (list[_AutoMap]): Parsed mappings describing dynamic fields.

    Returns:
        Callable[[dict], bool]: A filter to be passed to Loguru.
    """
    # 0. Pre-build the dict-filter predicate once (never per record) when needed.
    dict_filter: Optional[Callable[[_Record], bool]] = (
        _build_dict_filter(user_filter) if isinstance(user_filter, Mapping) else None
    )

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
            return "…" + value[-(width - 1) :]
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

            # 1.3. Truncate (if requested) before padding; otherwise hard-cut via precision
            if trunc:
                padded = _apply_align(_truncate(text, width, trunc), align, width)
            else:
                padded = _apply_align(text, align, width, precision=True)

            # 1.4. Attach computed placeholder into record.extra
            record["extra"][placeholder_key] = padded

        # 2. Evaluate the user-provided filter (callable delegated; dict applied; None passes)
        if callable(user_filter):
            return bool(user_filter(record))
        if dict_filter is not None:
            return dict_filter(record)
        return True

    # 3. Return the composed filter callable
    return built_filter
