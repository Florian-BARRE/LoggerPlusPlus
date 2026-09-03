# ====== Code Summary ======
# Color theme for the shipped formats. A Theme maps each themeable segment role to a
# loguru color tag; the default reproduces the historical colors exactly, so passing no
# theme leaves rendered output byte-identical. Color values are validated at construction
# so an invalid/empty/markup-bearing color fails fast with a clear, field-named error
# instead of crashing loguru's markup parser later inside add(). Level and message stay on
# loguru's dynamic `<level>` color and are intentionally not themeable.

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from typing import Optional

__all__: list[str] = ["Theme", "DEFAULT_THEME", "resolve_theme"]

# loguru's named foreground colors + their light- variants, plus text attributes.
_NAMED = frozenset(
    {
        "black",
        "red",
        "green",
        "yellow",
        "blue",
        "magenta",
        "cyan",
        "white",
    }
)
_NAMED = _NAMED | {f"light-{c}" for c in _NAMED}
_ATTRIBUTES = frozenset(
    {
        "bold",
        "dim",
        "normal",
        "italic",
        "underline",
        "strike",
        "blink",
        "reverse",
        "hide",
    }
)
_KNOWN = _NAMED | _ATTRIBUTES
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_EIGHT_BIT_RE = re.compile(r"^\d{1,3}$")


def _is_valid_color(color: str) -> bool:
    """Return True if `color` is a loguru color/attribute name, hex, or 8-bit code."""
    if not color:
        return False
    body = color[3:] if color.startswith(("fg ", "bg ")) else color
    return (
        body in _KNOWN or bool(_HEX_RE.match(body)) or bool(_EIGHT_BIT_RE.match(body))
    )


@dataclass(frozen=True)
class Theme:
    """
    Color tags (loguru markup names) for the themeable format segments.

    Each value must be a loguru color/attribute name (e.g. "red", "light-green", "dim"),
    an `fg `/`bg ` variant, a `#rrggbb` hex code, or an 8-bit code; an invalid value raises
    a clear `ValueError` naming the field at construction time.

    Attributes:
        timestamp (str): Color of the timestamp.
        identifier (str): Color of the identifier.
        name (str): Color of the source module name.
        line (str): Color of the source line number.
        process (str): Color of the process (PID) segment.
        thread (str): Color of the thread (TID) segment.
        separator (str): Color of the dimmed separators.
    """

    timestamp: str = "yellow"
    identifier: str = "light-green"
    name: str = "magenta"
    line: str = "light-magenta"
    process: str = "cyan"
    thread: str = "light-cyan"
    separator: str = "light-black"

    def __post_init__(self) -> None:
        """Validate every color field, failing fast with a field-named error."""
        for field in fields(self):
            value = getattr(self, field.name)
            if not _is_valid_color(value):
                raise ValueError(
                    f"Theme.{field.name}: {value!r} is not a valid loguru color/attribute"
                )


# The default theme — matches the colors the formats shipped with historically.
DEFAULT_THEME: Theme = Theme()


def resolve_theme(theme: Optional[Theme]) -> Theme:
    """
    Resolve a theme argument to a Theme, defaulting None and rejecting wrong types.

    Args:
        theme (Theme | None): A theme, or None to use the default.

    Returns:
        Theme: The resolved theme.

    Raises:
        TypeError: If `theme` is neither a Theme nor None.
    """
    if theme is None:
        return DEFAULT_THEME
    if not isinstance(theme, Theme):
        raise TypeError(f"theme must be a Theme or None, got {type(theme).__name__}")
    return theme
