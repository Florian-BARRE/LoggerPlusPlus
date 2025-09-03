# ====== Code Summary ======
# This module provides a utility function `fit_text` that applies truncation,
# alignment, and padding rules (via `FieldRule`) to format text consistently
# in log outputs.

# ====== Standard Library Imports ======
from __future__ import annotations

# ====== Local Project Imports ======
from ..core import FieldRule
from ..rules_enums import Truncate, Align


def fit_text(text: str, rule: FieldRule) -> str:
    """
    Fit text to the constraints defined in a FieldRule, applying truncation,
    padding, and alignment.

    Args:
        text (str): Input text to format.
        rule (FieldRule): Formatting rule specifying width, alignment, and truncation.

    Returns:
        str: The formatted string.
    """
    t = text

    # 1. Apply truncation if width is set and text exceeds it
    if 0 < rule.width < len(t):
        if rule.truncate == Truncate.HEAD:
            t = "…" + t[-(rule.width - 1):]
        elif rule.truncate == Truncate.MIDDLE:
            half = (rule.width - 1) // 2
            t = t[:half] + "…" + t[-(rule.width - 1 - half):]
        else:  # Truncate.TAIL
            t = t[: rule.width - 1] + "…"

    # 2. Apply padding and alignment if text is shorter than target width
    if rule.width > 0:
        pad = rule.width - len(t)
        if pad > 0:
            if rule.align == Align.LEFT:
                t = t + " " * pad
            elif rule.align == Align.CENTER:
                left = pad // 2
                right = pad - left
                t = " " * left + t + " " * right
            else:  # Align.RIGHT
                t = " " * pad + t

    return t
