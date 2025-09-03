# ====== Code Summary ======
# This module defines configuration for visual separators (e.g., log or console output dividers).
# It includes an enum of separator modes and a dataclass for holding separator settings.

from __future__ import annotations

# ====== Standard Library Imports ======
from enum import Enum
from dataclasses import dataclass


class SeparatorMode(str, Enum):
    """
    Enumeration of separator display modes.

    Options:
        THEME: Use theme-based separators (styling derived from theme).
        STATIC: Use a static ANSI string for the separator.
        DISABLED: No separator is displayed.
    """

    THEME = "theme"
    STATIC = "static"
    DISABLED = "disabled"


@dataclass(slots=True)
class SeparatorConfig:
    """
    Configuration for controlling how separators are displayed.

    Attributes:
        mode (SeparatorMode): Determines how separators are displayed.
        ansi (str | None): ANSI string to use when mode is STATIC. Ignored otherwise.
    """

    mode: SeparatorMode = SeparatorMode.THEME
    ansi: str | None = None  # used when STATIC
