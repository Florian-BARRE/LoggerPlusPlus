# ====== Code Summary ======
# This module defines two enumerations, `Align` and `Truncate`, used for
# controlling text formatting in logging. `Align` specifies alignment strategies,
# while `Truncate` specifies how to shorten text that exceeds the available width.

# ====== Standard Library Imports ======
from __future__ import annotations
from enum import StrEnum, auto


class Align(StrEnum):
    """
    Alignment options for formatting text fields.

    Members:
        LEFT: Left-align the text within its field.
        CENTER: Center-align the text within its field.
        RIGHT: Right-align the text within its field.
    """

    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


class Truncate(StrEnum):
    """
    Truncation strategies for text exceeding the allowed width.

    Members:
        HEAD: Remove characters from the start, keep the end.
        MIDDLE: Remove characters from the middle, keep start and end.
        TAIL: Remove characters from the end, keep the start.
    """

    HEAD = auto()
    MIDDLE = auto()
    TAIL = auto()
