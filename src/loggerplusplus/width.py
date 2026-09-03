# ====== Code Summary ======
# Visual-width text helpers for the auto-width engine. Column alignment must be
# measured in terminal cells, not code points: a full-width CJK glyph occupies two
# cells and a combining mark occupies zero. These pure functions (width, truncate,
# pad, hard-cut, render) let the registry and runtime align by visual width.
# Uses only the standard library `unicodedata` — no extra dependency.

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Optional

__all__: list[str] = [
    "visual_width",
    "truncate",
    "pad",
    "hard_cut",
    "render_field",
    "sanitize",
]

_ELLIPSIS: str = "…"
# Categories that render in zero terminal cells: non-spacing / enclosing marks,
# format characters (e.g. zero-width space/joiner, variation selectors) and controls.
_ZERO_WIDTH_CATEGORIES = frozenset({"Mn", "Me", "Cf", "Cc"})
_WIDE_EAW = frozenset({"W", "F"})

# ANSI / VT escape sequences (CSI colour codes like "\x1b[31m", plus simple escapes).
_ANSI_RE: re.Pattern[str] = re.compile(r"\x1b(?:\[[0-9;?]*[ -/]*[@-~]|[@-Z\\-_])")

# NOTE on grapheme clusters: width is measured per code point, not per grapheme.
# A ZWJ emoji sequence (e.g. a family emoji) or an emoji with a skin-tone modifier
# is drawn by a terminal as a single 2-cell glyph but scores 2 cells per component
# here, so such values can reserve a slightly-too-wide column. A correct fix needs
# grapheme segmentation (a third-party dependency), which this package deliberately
# avoids; this is a documented limitation, not a bug.


def sanitize(value: str) -> str:
    """
    Strip control sequences so a value cannot break or poison a log line.

    Removes ANSI/VT escape sequences and C0/C1 control characters (category `Cc`,
    e.g. newline, tab, NUL, ESC). Without this, a control character in an identifier
    would be measured as zero cells yet emitted literally — splitting a record across
    lines (log injection) or, for a raw escape, poisoning the shared auto-width column.
    Applied once, before both width measurement and rendering, so they never diverge.

    Args:
        value (str): The raw field value.

    Returns:
        str: The value with escape sequences and control characters removed.
    """
    # 1. Drop full ANSI/VT escape sequences, then any remaining C0/C1 controls.
    value = _ANSI_RE.sub("", value)
    return "".join(c for c in value if unicodedata.category(c) != "Cc")


@lru_cache(maxsize=None)
def _char_width(char: str) -> int:
    """
    Return the terminal-cell width of a single character (0, 1, or 2).

    Args:
        char (str): A single character.

    Returns:
        int: 0 for combining/zero-width, 2 for East-Asian wide/fullwidth, else 1.
    """
    if unicodedata.category(char) in _ZERO_WIDTH_CATEGORIES:
        return 0
    if unicodedata.east_asian_width(char) in _WIDE_EAW:
        return 2
    return 1


def visual_width(value: str) -> int:
    """
    Return the total terminal-cell width of `value`.

    Args:
        value (str): The string to measure.

    Returns:
        int: Sum of per-character cell widths.
    """
    return sum(_char_width(c) for c in value)


def _cut_head(value: str, budget: int) -> str:
    """Keep the longest prefix whose visual width is <= `budget`."""
    # 1. Accumulate characters until the next one would overflow the cell budget.
    out: list[str] = []
    used: int = 0
    for c in value:
        w = _char_width(c)
        if used + w > budget:
            break
        out.append(c)
        used += w
    return "".join(out)


def _cut_tail(value: str, budget: int) -> str:
    """Keep the longest suffix whose visual width is <= `budget`."""
    # 1. Same as _cut_head but walking from the end, then restore order.
    out: list[str] = []
    used: int = 0
    for c in reversed(value):
        w = _char_width(c)
        if used + w > budget:
            break
        out.append(c)
        used += w
    return "".join(reversed(out))


def hard_cut(value: str, width: int) -> str:
    """
    Hard-cut `value` to at most `width` cells, without an ellipsis.

    Args:
        value (str): Source string.
        width (int): Target cell width.

    Returns:
        str: The longest prefix fitting in `width` cells.
    """
    if visual_width(value) <= width:
        return value
    return _cut_head(value, width)


def truncate(value: str, width: int, mode: str) -> str:
    """
    Truncate `value` to `width` cells using `mode`, inserting an ellipsis.

    Args:
        value (str): Source string.
        width (int): Target cell width (>= 0).
        mode (str): One of {"left", "right", "middle"}; any other value hard-cuts.

    Returns:
        str: The truncated string (visual width <= `width`).
    """
    # 1. Nothing to do when it already fits.
    if visual_width(value) <= width:
        return value

    # 2. No room for an ellipsis: fall back to a plain head cut.
    if width <= 1:
        return _cut_head(value, width)

    # 3. Reserve one cell for the ellipsis, then keep the requested side(s).
    budget = width - 1
    if mode == "right":
        return _cut_head(value, budget) + _ELLIPSIS
    if mode == "left":
        return _ELLIPSIS + _cut_tail(value, budget)
    if mode == "middle":
        left_budget = budget // 2
        right_budget = budget - left_budget
        return (
            _cut_head(value, left_budget) + _ELLIPSIS + _cut_tail(value, right_budget)
        )

    # 4. Unknown mode: hard cut to the full width.
    return _cut_head(value, width)


def pad(value: str, width: int, align: str) -> str:
    """
    Pad `value` with spaces to `width` cells for the given alignment.

    Args:
        value (str): String to pad (assumed to already fit within `width`).
        width (int): Target cell width.
        align (str): ">" (right), "^" (center), anything else left.

    Returns:
        str: The padded string; returned unchanged if it already fills the width.
    """
    # 1. No padding when the value already meets or exceeds the width.
    gap = width - visual_width(value)
    if gap <= 0:
        return value

    # 2. Distribute the gap according to the alignment.
    if align == ">":
        return " " * gap + value
    if align == "^":
        left = gap // 2
        return " " * left + value + " " * (gap - left)
    return value + " " * gap


def render_field(text: str, width: int, align: str, trunc: Optional[str]) -> str:
    """
    Fit `text` into a `width`-cell column: truncate (or hard-cut), then pad.

    Args:
        text (str): The value to render.
        width (int): Target cell width.
        align (str): Alignment glyph (">", "^", else left).
        trunc (str | None): Truncation mode, or None to hard-cut overflow.

    Returns:
        str: The rendered, width-aligned column value.
    """
    body = truncate(text, width, trunc) if trunc else hard_cut(text, width)
    return pad(body, width, align)
