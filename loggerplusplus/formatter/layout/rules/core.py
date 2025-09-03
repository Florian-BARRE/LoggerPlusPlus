# ====== Code Summary ======
# This module defines the `FieldRule` dataclass, which encapsulates formatting
# rules for log fields such as width, alignment, truncation, and coloring options.

# ====== Standard Library Imports ======
from __future__ import annotations
from dataclasses import dataclass

# ====== Local Project Imports ======
from .rules_enums import Align, Truncate


@dataclass(slots=True)
class FieldRule:
    """
    Defines rules for shaping and formatting a log field.

    Attributes:
        width (int): Desired width of the field (0 = no constraint).
        align (Align): Alignment strategy (default: left).
        truncate (Truncate): Truncation strategy if text exceeds width.
        reserve_lineno (bool): Reserve space for line numbers when formatting filenames.
        color_ansi (str | None): Optional ANSI color code for coloring field text.
        disable_color (bool): If True, disables ANSI coloring even if color_ansi is set.
        auto_width (bool): Automatically adjust width based on observed field lengths.
        min_width (int): Minimum width allowed if auto_width is enabled.
        max_width (int | None): Maximum width allowed if auto_width is enabled.
    """

    width: int
    align: Align = Align.LEFT
    truncate: Truncate = Truncate.TAIL
    reserve_lineno: bool = False
    color_ansi: str | None = None
    disable_color: bool = False
    auto_width: bool = False
    min_width: int = 0
    max_width: int | None = None
